"""Run fine-tuned PyTorch xView2 damage inference on one pre/post pair.

The upstream trainer (michal2409/xView2) only knows how to evaluate a dataset
directory, not a single image pair, so this script stages the pair into a
throwaway holdout layout, shells out to ``main.py --exec_mode eval``, and reads
back the saved probability tensor.

Two artifacts come out:

* ``--out``                       the class mask (0-4), same encoding as every
                                  other inference mode in this repo.
* ``{out_stem}_confidence.npy``   per-pixel probability of the winning class.

Only this mode can produce confidence. The TF 1.15 Docker baseline and the stub
emit label masks with no probabilities behind them.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
XVIEW2_ROOT = REPO_ROOT / "ml" / "pytorch-xview2"
MAIN_PY = XVIEW2_ROOT / "main.py"

NUM_DAMAGE_CLASSES = 5
TILE_SIZE = 1024


def probs_to_mask_and_confidence(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """Split a model output tensor into a class mask and a confidence map.

    ``arr`` is (C, H, W) post-softmax probabilities as written by the upstream
    ``model/plt.py``. Applying softmax again here would squash the distribution
    toward uniform and silently deflate every confidence value, so we only ever
    take the max — never re-normalize.

    A 2-D ``arr`` means the checkpoint emitted labels rather than probabilities;
    there is no confidence to report in that case.
    """
    if arr.ndim == 3:
        mask = np.argmax(arr, axis=0).astype(np.uint8)
        confidence = np.take_along_axis(arr, mask[None, :, :], axis=0)[0].astype(np.float32)
        return np.clip(mask, 0, NUM_DAMAGE_CLASSES - 1), confidence

    # Clip in float: casting a negative value to uint8 wraps it around, and a
    # subsequent clip would then read -3 as 253 and call it "destroyed".
    mask = np.clip(np.round(arr), 0, NUM_DAMAGE_CLASSES - 1).astype(np.uint8)
    return mask, None


def confidence_path_for(out_mask: Path) -> Path:
    """Must stay in sync with backend/app/services/inference.py."""
    return out_mask.parent / f"{out_mask.stem}_confidence.npy"


def _placeholder_target(path: Path) -> None:
    """Eval still demands a target mask; the metrics computed against it are discarded."""
    Image.fromarray(np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.uint8)).save(path)


def _stage_holdout(pre_path: Path, post_path: Path, work: Path) -> Path:
    """Lay the pair out the way the upstream dataset loader expects."""
    data_root = work / "data"
    holdout = data_root / "holdout"
    images = holdout / "images"
    targets = holdout / "targets"
    for directory in (images, targets):
        directory.mkdir(parents=True, exist_ok=True)

    stem = post_path.stem.replace("_post_disaster", "")
    pre_name = f"{stem}_pre_disaster.png"
    post_name = f"{stem}_post_disaster.png"

    shutil.copy2(pre_path, images / pre_name)
    shutil.copy2(post_path, images / post_name)
    _placeholder_target(targets / pre_name)
    _placeholder_target(targets / post_name)

    return data_root


def infer_pair(
    pre_path: Path,
    post_path: Path,
    checkpoint: Path,
    out_mask: Path,
    work_dir: Path | None = None,
) -> Path:
    if not MAIN_PY.exists():
        raise FileNotFoundError(
            f"Missing {MAIN_PY} — clone michal2409/xView2 into ml/pytorch-xview2 "
            "and run ml/finetune/patch_pytorch_xview2.py"
        )
    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")

    work = work_dir or (REPO_ROOT / "backend" / "outputs" / f"pytorch_{uuid.uuid4().hex[:8]}")
    data_root = _stage_holdout(pre_path, post_path, work)
    results = work / "results"
    results.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(MAIN_PY),
        "--exec_mode", "eval",
        "--type", "post",
        "--dmg_model", "siamese",
        "--encoder", "resnet50",
        "--loss_str", "focal+dice",
        "--data", str(data_root),
        "--results", str(results),
        "--ckpt", str(checkpoint),
        "--gpus", "0",
        "--val_batch_size", "1",
        "--num_workers", "0",
    ]

    env = {**os.environ, "PYTHONPATH": str(XVIEW2_ROOT)}
    index_csv = XVIEW2_ROOT / "utils" / "index.csv"
    if index_csv.exists():
        env["XVIEW2_INDEX_CSV"] = str(index_csv.resolve())

    subprocess.run(command, check=True, cwd=str(XVIEW2_ROOT), env=env)

    predictions = sorted((results / "probs").glob("test_damage_*.npy"))
    if not predictions:
        raise RuntimeError(f"No damage predictions written to {results / 'probs'}")

    mask, confidence = probs_to_mask_and_confidence(np.load(predictions[0]))

    out_mask.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask, mode="L").save(out_mask)
    if confidence is not None:
        np.save(confidence_path_for(out_mask), confidence)

    return out_mask


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre", type=Path, required=True)
    parser.add_argument("--post", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    out = infer_pair(args.pre, args.post, args.checkpoint, args.out)
    print(f"Wrote mask: {out}")


if __name__ == "__main__":
    main()
