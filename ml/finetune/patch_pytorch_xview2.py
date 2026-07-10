"""Port michal2409/xView2 (2020) to a modern Python / PyTorch stack.

Upstream targets Python 3.7, torch 1.x, PyTorch Lightning 1.0 and NVIDIA Apex.
Nothing in that list installs cleanly on Python 3.11 + torch 2.x, which is what
AMD ROCm images and Kaggle both ship. Each patch below fixes one incompatibility:

    data_loading/pytorch_loader.py  hardcoded /workspace index.csv -> env override
    model/plt.py                    apex.optimizers -> torch.optim
    model/unet.py                   ResNeSt import made optional (we use resnet50)
    utils/f1.py                     pl.metrics.Metric -> torchmetrics.Metric
    main.py                         PL 1.9 Trainer API + guard NVML affinity call
    model/loss.py                   replaced wholesale (see overrides/model/loss.py)

Every patch is idempotent: applying it twice is a no-op, and a patch whose anchor
text is missing raises rather than pretending to succeed — a silent no-op here
surfaces later as an incomprehensible CUDA error thirty minutes into training.

Usage, after cloning upstream into ml/pytorch-xview2/:

    python ml/finetune/patch_pytorch_xview2.py
    python ml/finetune/patch_pytorch_xview2.py --check   # verify only
"""

from __future__ import annotations

import argparse
import py_compile
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
XVIEW2_ROOT = REPO_ROOT / "ml" / "pytorch-xview2"
OVERRIDES = Path(__file__).resolve().parent / "overrides"


class PatchError(RuntimeError):
    pass


def _read(path: Path) -> str:
    if not path.exists():
        raise PatchError(f"Expected upstream file is missing: {path}")
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _substitute(path: Path, anchor: str, replacement: str, marker: str) -> bool:
    """Replace `anchor` with `replacement`. Returns False if already patched."""
    text = _read(path)
    if marker in text:
        return False
    if anchor not in text:
        raise PatchError(
            f"{path.name}: anchor not found, upstream may have changed.\n  anchor: {anchor[:70]!r}"
        )
    _write(path, text.replace(anchor, replacement, 1))
    return True


def _prepend(path: Path, block: str, marker: str) -> bool:
    text = _read(path)
    if marker in text:
        return False
    _write(path, block.lstrip("\n") + "\n" + text)
    return True


MARKER = "# DisasterIQ patch"


def patch_index_csv(root: Path) -> bool:
    """Upstream hardcodes /workspace/xview2/utils/index.csv."""
    path = root / "data_loading" / "pytorch_loader.py"
    helper = f'''
{MARKER}: index.csv location is configurable so a subset index can be used.
import os as _os
import pandas as _pd


def _load_index_csv():
    default = _os.path.join(_os.path.dirname(__file__), "..", "utils", "index.csv")
    return _pd.read_csv(_os.environ.get("XVIEW2_INDEX_CSV", default))
'''
    call_site = "data_frame = _load_index_csv()"
    text = _read(path)

    # The helper's own `def _load_index_csv()` must not be mistaken for the
    # rewritten call site, so key idempotency off the call, not the definition.
    if call_site in text:
        return False

    hardcoded = [
        line
        for line in text.splitlines()
        if "read_csv(" in line and "index.csv" in line and "_load_index_csv" not in line
    ]
    if not hardcoded:
        raise PatchError(f"{path.name}: could not find the hardcoded index.csv read")

    _prepend(path, helper, f"{MARKER}: index.csv")
    text = _read(path)
    for line in hardcoded:
        indent = line[: len(line) - len(line.lstrip())]
        text = text.replace(line, f"{indent}{call_site}", 1)
    _write(path, text)
    return True


def patch_apex(root: Path) -> bool:
    """Apex is NVIDIA-only and unbuildable on ROCm; torch.optim covers our needs."""
    path = root / "model" / "plt.py"
    return _substitute(
        path,
        "from apex.optimizers import FusedAdam, FusedNovoGrad, FusedSGD",
        f"{MARKER}: apex is CUDA-only and unavailable on ROCm.\n"
        "from torch.optim import SGD as FusedSGD\n"
        "from torch.optim import Adam as FusedAdam\n"
        "from torch.optim import Adam as FusedNovoGrad",
        f"{MARKER}: apex",
    )


def patch_resnest(root: Path) -> bool:
    """ResNeSt pulls a heavy dep we never use; make the import optional."""
    path = root / "model" / "unet.py"
    text = _read(path)
    if f"{MARKER}: resnest" in text:
        return False
    for anchor in ("from resnest.torch import resnest50", "import resnest"):
        if anchor in text:
            replacement = (
                f"{MARKER}: resnest is optional; we train with the resnet50 encoder.\n"
                "try:\n"
                f"    {anchor}\n"
                "except ImportError:  # pragma: no cover\n"
                "    resnest50 = None"
            )
            _write(path, text.replace(anchor, replacement, 1))
            return True
    return False


def patch_torchmetrics(root: Path) -> bool:
    """pytorch_lightning.metrics was removed in PL 1.5 and split into torchmetrics."""
    path = root / "utils" / "f1.py"
    text = _read(path)
    if f"{MARKER}: torchmetrics" in text:
        return False
    for anchor in (
        "from pytorch_lightning.metrics import Metric",
        "from pytorch_lightning.metrics.metric import Metric",
    ):
        if anchor in text:
            _write(
                path,
                text.replace(
                    anchor,
                    f"{MARKER}: torchmetrics — PL dropped .metrics in 1.5.\n"
                    "from torchmetrics import Metric",
                    1,
                ),
            )
            return True
    raise PatchError(f"{path.name}: no pytorch_lightning.metrics import to rewrite")


def patch_trainer_api(root: Path) -> bool:
    """PL 1.9 renamed accelerator->strategy and dropped the checkpoint_callback flag."""
    path = root / "main.py"
    text = _read(path)
    if f"{MARKER}: trainer" in text:
        return False

    patched = text
    replacements = [
        ("checkpoint_callback=", "enable_checkpointing="),
        ("accelerator=args.distribution_mode", "strategy=args.distribution_mode"),
        ("accelerator='ddp'", "strategy='ddp'"),
        ('accelerator="ddp"', 'strategy="ddp"'),
    ]
    applied = False
    for old, new in replacements:
        if old in patched:
            patched = patched.replace(old, new)
            applied = True

    if not applied:
        raise PatchError("main.py: no PL Trainer arguments matched; upstream may have changed")

    _write(path, f"{MARKER}: trainer args ported to PyTorch Lightning 1.9.\n" + patched)
    return True


def patch_loss(root: Path) -> bool:
    """Wholesale replacement — see overrides/model/loss.py for the reasoning."""
    source = OVERRIDES / "model" / "loss.py"
    target = root / "model" / "loss.py"
    if not source.exists():
        raise PatchError(f"Missing override: {source}")
    if target.exists() and target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8"):
        return False
    backup = target.with_suffix(".py.orig")
    if target.exists() and not backup.exists():
        shutil.copy2(target, backup)
    shutil.copy2(source, target)
    return True


PATCHES = (
    ("index.csv path", patch_index_csv),
    ("apex optimizers", patch_apex),
    ("resnest import", patch_resnest),
    ("torchmetrics", patch_torchmetrics),
    ("trainer api", patch_trainer_api),
    ("loss override", patch_loss),
)

COMPILE_TARGETS = (
    "data_loading/pytorch_loader.py",
    "model/plt.py",
    "model/unet.py",
    "model/loss.py",
    "utils/f1.py",
    "main.py",
)


def verify_compiles(root: Path) -> None:
    for rel in COMPILE_TARGETS:
        path = root / rel
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            raise PatchError(f"{rel} does not compile after patching:\n{exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=XVIEW2_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify the patched tree compiles; apply nothing.",
    )
    args = parser.parse_args()

    if not (args.repo / "main.py").exists():
        print(
            f"error: {args.repo} is not an xView2 checkout.\n"
            "  git clone https://github.com/michal2409/xView2 ml/pytorch-xview2",
            file=sys.stderr,
        )
        return 1

    if args.check:
        verify_compiles(args.repo)
        print("All patched files compile.")
        return 0

    for name, patch in PATCHES:
        try:
            changed = patch(args.repo)
        except PatchError as exc:
            print(f"error: {name}: {exc}", file=sys.stderr)
            return 1
        print(f"  {'applied ' if changed else 'already '} {name}")

    verify_compiles(args.repo)
    print("Patched. Next: python scripts/generate_subset_index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
