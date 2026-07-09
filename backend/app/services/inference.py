"""Inference adapter: stub demo inference or Docker baseline inference.

This file owns:
1. demo-pair discovery
2. demo image path resolution
3. inference execution

Important:
- /demo/pairs, /demo/images, and /analyze must agree about where demo files live.
- main.py expects run_inference(pre_path, post_path, out_dir) -> (mask_path, mode).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import settings


def _demo_search_dirs() -> list[Path]:
    """Folders where demo image pairs may exist."""
    return [
        settings.demo_data_dir / "images",
        settings.upload_dir,
    ]


def _infer_disaster_type(base: str) -> str:
    lowered = base.lower()

    if "earthquake" in lowered:
        return "earthquake"
    if "flooding" in lowered or "flood" in lowered:
        return "flood"
    if "fire" in lowered or "wildfire" in lowered:
        return "wildfire"

    return base.split("_")[0] if "_" in base else base


def list_demo_pairs() -> list[dict[str, str]]:
    """Return all before/after demo pairs.

    Expected naming:
        <id>_pre_disaster.png
        <id>_post_disaster.png

    Example:
        demo_pre_disaster.png
        demo_post_disaster.png
    """
    pairs: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for images_dir in _demo_search_dirs():
        if not images_dir.exists():
            continue

        for pre in sorted(images_dir.glob("*_pre_disaster.png")):
            base = pre.name.replace("_pre_disaster.png", "")
            post = images_dir / f"{base}_post_disaster.png"

            if not post.exists():
                continue

            if base in seen_ids:
                continue

            seen_ids.add(base)

            pairs.append(
                {
                    "id": base,
                    "disaster_type": _infer_disaster_type(base),
                    "pre_image": pre.name,
                    "post_image": post.name,
                }
            )

    return pairs


def resolve_demo_pair(pair_id: str) -> dict[str, Path | str]:
    """Resolve a demo pair ID into real image paths."""
    clean_id = Path(pair_id).name

    for images_dir in _demo_search_dirs():
        pre = images_dir / f"{clean_id}_pre_disaster.png"
        post = images_dir / f"{clean_id}_post_disaster.png"

        if pre.exists() and post.exists():
            return {
                "id": clean_id,
                "disaster_type": _infer_disaster_type(clean_id),
                "pre_path": pre,
                "post_path": post,
                "pre_image": pre.name,
                "post_image": post.name,
            }

    raise FileNotFoundError(f"Demo pair not found: {pair_id}")


def resolve_demo_image(filename: str) -> Path:
    """Resolve a demo image filename from any allowed demo folder."""
    clean_name = Path(filename).name

    for images_dir in _demo_search_dirs():
        candidate = images_dir / clean_name

        if candidate.exists() and candidate.is_file():
            return candidate

    raise FileNotFoundError(f"Demo image not found: {filename}")


def _make_stub_mask(post_image_path: Path, out_dir: Path) -> Path:
    """Create a deterministic fake damage mask.

    Pixel values match the xView2 scheme used by scoring.py:
        0 = background (no building)
        1 = none (undamaged building)
        2 = minor
        3 = major
        4 = destroyed

    This keeps the current backend scoring pipeline working.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    image = Image.open(post_image_path).convert("RGB")
    width, height = image.size

    mask = np.zeros((height, width), dtype=np.uint8)

    # Deterministic zones for demo mode.
    # Top-left: minor
    mask[
        int(height * 0.08) : int(height * 0.32),
        int(width * 0.08) : int(width * 0.34),
    ] = 2

    # Center: major
    mask[
        int(height * 0.35) : int(height * 0.68),
        int(width * 0.35) : int(width * 0.68),
    ] = 3

    # Bottom-right: destroyed
    mask[
        int(height * 0.58) : int(height * 0.90),
        int(width * 0.62) : int(width * 0.92),
    ] = 4

    # Add a second destroyed region so priority zones look less empty.
    mask[
        int(height * 0.18) : int(height * 0.38),
        int(width * 0.70) : int(width * 0.88),
    ] = 4

    mask_path = out_dir / "damage_mask.png"
    Image.fromarray(mask).save(mask_path)

    return mask_path


def _run_docker_baseline(pre_image_path: Path, post_image_path: Path, out_dir: Path) -> Path:
    """Run Docker baseline inference if configured.

    This keeps the adapter honest: demo/stub mode works locally, Docker mode
    only works if the baseline container is actually available.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    if not settings.xview2_docker_image:
        raise RuntimeError("xview2_docker_image is not configured")

    run_id = out_dir.name or "job"

    # The image entrypoint is the upstream xView2 run.sh, which takes POSITIONAL
    # arguments: <pre> <post> <localization_out> <classification_out>. The
    # baseline path is already supplied by the image ENTRYPOINT, so we only append
    # these four paths. Pre and post must share a directory (they always do in
    # this app) so a single read-only /input mount covers both.
    if pre_image_path.parent.resolve() != post_image_path.parent.resolve():
        raise RuntimeError("pre and post images must be in the same directory for docker inference")

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{pre_image_path.parent.resolve()}:/input:ro",
        "-v",
        f"{out_dir.resolve()}:/output",
        settings.xview2_docker_image,
        f"/input/{pre_image_path.name}",
        f"/input/{post_image_path.name}",
        f"/output/{run_id}_localization.png",
        f"/output/{run_id}_mask.png",
    ]

    subprocess.run(command, check=True)

    mask_path = out_dir / f"{run_id}_mask.png"

    if not mask_path.exists():
        raise RuntimeError(f"Docker baseline did not produce mask: {mask_path}")

    return mask_path


def run_inference(pre_image_path: Path, post_image_path: Path, out_dir: Path) -> tuple[Path, str]:
    """Main inference entry point.

    main.py expects:
        mask_path, mode = run_inference(pre_path, post_path, out_dir)
    """
    if settings.inference_mode == "stub":
        mask_path = _make_stub_mask(post_image_path, out_dir)
        return mask_path, "stub"

    if settings.inference_mode == "docker":
        mask_path = _run_docker_baseline(pre_image_path, post_image_path, out_dir)
        return mask_path, "docker"

    raise RuntimeError(f"Unsupported inference_mode: {settings.inference_mode}")