"""Drop-in replacement for michal2409/xView2 ``model/loss.py``.

Why this exists: upstream gathers building pixels into a flat ``[N, C]`` tensor
before computing the damage loss, but MONAI 1.x ``FocalLoss``/``DiceLoss``
assume a spatial ``B x C x H x W`` layout and raise shape errors on that input.

So we split by rank:

* damage (flattened, ``y_pred.dim() == 2``)  -> plain PyTorch focal / dice
* localization (spatial, ``dim() == 4``)     -> MONAI, which is happy there

Copied into ml/pytorch-xview2/model/loss.py by patch_pytorch_xview2.py.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from monai.losses import DiceLoss, FocalLoss

SMOOTH = 1e-6
FOCAL_GAMMA = 2.0


class MonaiLoss(nn.Module):
    """Focal or dice, dispatched on tensor rank."""

    def __init__(self, loss: str):
        super().__init__()
        self.loss = loss
        self.focal = FocalLoss(gamma=FOCAL_GAMMA, use_softmax=True, to_onehot_y=True)
        self.dice_bg = DiceLoss(include_background=True, softmax=True, to_onehot_y=True, batch=True)
        self.dice_nbg = DiceLoss(
            include_background=False, softmax=True, to_onehot_y=True, batch=True
        )

    @staticmethod
    def _flat_focal(y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        n_classes = y_pred.shape[1]
        y_true = y_true.long().clamp(0, n_classes - 1)
        log_prob = F.log_softmax(y_pred, dim=1)
        ce = F.nll_loss(log_prob, y_true, reduction="none")
        pt = log_prob.exp().gather(1, y_true.unsqueeze(1)).squeeze(1)
        return ((1 - pt) ** FOCAL_GAMMA * ce).mean()

    @staticmethod
    def _flat_dice(
        y_pred: torch.Tensor,
        y_true: torch.Tensor,
        *,
        include_background: bool,
    ) -> torch.Tensor:
        n_classes = y_pred.shape[1]
        y_true = y_true.long().clamp(0, n_classes - 1)
        probs = F.softmax(y_pred, dim=1)
        onehot = F.one_hot(y_true, num_classes=n_classes).float()

        first_class = 0 if include_background else 1
        dice_total = y_pred.new_zeros(())
        counted = 0
        for cls in range(first_class, n_classes):
            pred_c = probs[:, cls]
            true_c = onehot[:, cls]
            intersection = (pred_c * true_c).sum()
            dice_total = dice_total + (2 * intersection + SMOOTH) / (
                pred_c.sum() + true_c.sum() + SMOOTH
            )
            counted += 1

        return 1 - dice_total / max(counted, 1)

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        # Damage: already gathered to [N, C]. MONAI cannot handle this rank.
        if y_pred.dim() == 2:
            if y_true.dim() == 2 and y_true.shape[1] == 1:
                y_true = y_true.squeeze(1)
            if self.loss == "focal":
                return self._flat_focal(y_pred, y_true)
            # Binary localization keeps background; 4-class damage drops it,
            # because "not a building" is not a damage grade to optimize for.
            return self._flat_dice(y_pred, y_true, include_background=y_pred.shape[1] == 2)

        # Localization: standard spatial layout.
        if y_true.dim() == 3:
            y_true = y_true.unsqueeze(1)
        y_true = y_true.float()

        if self.loss == "dice":
            return self.dice_nbg(y_pred, y_true) if y_pred.shape[1] == 2 else self.dice_bg(
                y_pred, y_true
            )
        return self.focal(y_pred, y_true)


class Ohem(nn.Module):
    """Online hard-example mining: keep all positives, plus the worst negatives."""

    def __init__(self, fraction: float | None = None):
        super().__init__()
        self.loss = nn.CrossEntropyLoss(reduction="none")
        self.fraction = fraction

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        batch_size = y_true.size(0)
        losses = self.loss(y_pred, y_true).view(batch_size, -1)
        positive_mask = (y_true > 0).view(batch_size, -1)

        n_positive = torch.sum(positive_mask, dim=1)
        n_negative = torch.sum(~positive_mask, dim=1)
        n_hard_negative = torch.max((n_negative / 4).clamp_min(5), 2 * n_positive)

        total = y_pred.new_zeros(())
        num_samples = 0
        for i in range(batch_size):
            positives = losses[i, positive_mask[i]]
            negatives = losses[i, ~positive_mask[i]]
            hardest, _ = negatives.sort(descending=True)
            hardest = hardest[: int(n_hard_negative[i])]
            total = total + positives.sum() + hardest.sum()
            num_samples += positives.numel() + hardest.numel()

        return total / float(max(num_samples, 1))


class CORAL(nn.Module):
    """Ordinal regression: damage grades are ranked, not merely distinct."""

    def __init__(self):
        super().__init__()
        self.register_buffer(
            "levels",
            torch.tensor([[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]], dtype=torch.float32),
        )

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        levels = self.levels[y_true].to(y_pred.device)
        logpt = F.logsigmoid(y_pred)
        loss = torch.sum(logpt * levels + (logpt - y_pred) * (1 - levels), dim=1)
        return -torch.mean(loss)


def _build_losses() -> dict[str, nn.Module]:
    return {
        "dice": MonaiLoss("dice"),
        "focal": MonaiLoss("focal"),
        "ce": nn.CrossEntropyLoss(),
        "ohem": Ohem(),
        "mse": nn.MSELoss(),
        "coral": CORAL(),
    }


class Loss(nn.Module):
    """Sum of the losses named in ``args.loss_str`` (e.g. ``focal+dice``)."""

    def __init__(self, args):
        super().__init__()
        self.loss_str = args.loss_str
        self.post = args.type == "post"
        available = _build_losses()
        self.losses = nn.ModuleList([available[name] for name in self.loss_str.split("+")])

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        if self.post:
            # Damage is only defined on building pixels. Gather them, then shift
            # labels 1-4 down to logits 0-3. Clamp absorbs 255 nodata artifacts
            # and the fractional values bilinear label downsampling can produce.
            mask = y_true > 0
            y_pred = torch.stack([y_pred[:, i][mask] for i in range(y_pred.shape[1])], dim=1)
            y_true = (y_true[mask].float() - 1).round().clamp(0, y_pred.shape[1] - 1)

        if self.loss_str == "mse":
            y_pred = F.relu(y_pred[:, 0])
            y_true = y_true.float()
        else:
            y_true = y_true.long()

        total = y_pred.new_zeros(())
        for loss_fn in self.losses:
            total = total + loss_fn(y_pred, y_true)
        return total
