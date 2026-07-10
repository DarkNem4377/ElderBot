"""Build the index.csv the xView2 loader reads, for a training subset.

Upstream's ``utils/generate_idx.py`` assumes the full ~8k-pair train set and
writes indices against it. We fine-tune on a hazard-filtered subset, so the
``idx`` column has to be renumbered against the sorted image list of *that*
directory or the loader reads the wrong tiles.

Usage:
  python scripts/generate_subset_index.py \\
      --data-dir data/train_subset \\
      --out ml/pytorch-xview2/utils/index.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PRE_SUFFIX = "_pre_disaster.png"
POST_SUFFIX = "_post_disaster.png"


def find_pairs(images_dir: Path) -> list[str]:
    """Return sorted stems that have both a pre and a post image."""
    if not images_dir.is_dir():
        raise SystemExit(f"Not a directory: {images_dir}")

    stems = []
    for pre in sorted(images_dir.glob(f"*{PRE_SUFFIX}")):
        stem = pre.name[: -len(PRE_SUFFIX)]
        if (images_dir / f"{stem}{POST_SUFFIX}").exists():
            stems.append(stem)
    return stems


def write_index(stems: list[str], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["idx", "name"])
        for idx, stem in enumerate(stems):
            writer.writerow([idx, stem])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    images_dir = args.data_dir / "images"
    if not images_dir.is_dir():
        images_dir = args.data_dir

    stems = find_pairs(images_dir)
    if not stems:
        raise SystemExit(f"No pre/post pairs found under {images_dir}")

    write_index(stems, args.out)
    print(f"Wrote {len(stems)} pairs to {args.out}")


if __name__ == "__main__":
    main()
