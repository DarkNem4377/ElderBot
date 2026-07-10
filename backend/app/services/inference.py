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
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from app.config import settings

DOCKER_TIMEOUT_SECONDS = 600
PYTORCH_TIMEOUT_SECONDS = 600

# Pixels differing by less than this are lighting/registration noise, never damage.
MIN_DIFF_THRESHOLD = 15.0
DIFF_PERCENTILE = 92


def _demo_search_dirs() -> list[Path]:
    """Folders where demo image pairs may exist.

    Deliberately excludes the upload dir: /demo/images serves anything found
    here by filename, and per-analysis uploads are not public content.
    """
    return [settings.demo_data_dir / "images"]


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


def resolve_demo_target(post_image_path: Path) -> Path | None:
    """Find the xBD ground-truth damage mask for a post-disaster image, if any."""
    stem = post_image_path.stem.replace("_post_disaster", "")
    target_name = f"{stem}_post_disaster_target.png"

    for root in (settings.demo_data_dir, settings.test_data_dir):
        candidate = root / "targets" / target_name
        if candidate.exists():
            return candidate

    return None


def _diff_mask(pre_image_path: Path, post_image_path: Path, out_path: Path) -> Path:
    """Derive a damage mask from the pre/post brightness difference.

    A stand-in for a real model when no ground truth exists: pixels that
    changed a lot between the two captures are treated as damaged, and the
    magnitude of the change picks the severity class. The threshold is a high
    percentile of the difference, so the mask adapts to each image pair rather
    than assuming a fixed brightness scale.
    """
    pre = np.array(Image.open(pre_image_path).convert("L"), dtype=np.float32)
    post_image = Image.open(post_image_path).convert("L")

    if post_image.size != (pre.shape[1], pre.shape[0]):
        post_image = post_image.resize((pre.shape[1], pre.shape[0]))

    post = np.array(post_image, dtype=np.float32)

    diff = np.abs(post - pre)
    threshold = max(MIN_DIFF_THRESHOLD, float(np.percentile(diff, DIFF_PERCENTILE)))

    # When more than (100 - DIFF_PERCENTILE)% of the frame changed, the
    # percentile lands *inside* the changed region and thresholding above it
    # would erase the very damage we are looking for. Keep the threshold
    # strictly below the peak difference so a heavily damaged scene still
    # produces a mask.
    peak = float(diff.max())
    if peak > MIN_DIFF_THRESHOLD:
        threshold = min(threshold, peak - 1e-3)

    # Thresholding alone leaves single-pixel speckle that connected-component
    # labeling would then count as thousands of "buildings". Opening erases
    # anything thinner than the structuring element before that happens.
    damaged = ndimage.binary_opening(diff > threshold, structure=np.ones((3, 3)))

    mask = np.zeros(pre.shape, dtype=np.uint8)
    severity = np.full(diff[damaged].shape, 2, dtype=np.uint8)
    severity[diff[damaged] > threshold * 1.5] = 3
    severity[diff[damaged] > threshold * 2.2] = 4
    mask[damaged] = severity

    Image.fromarray(mask, mode="L").save(out_path)
    return out_path


def _make_stub_mask(pre_image_path: Path, post_image_path: Path, out_dir: Path) -> tuple[Path, str]:
    """Produce a damage mask without a trained model.

    Prefers the xBD ground-truth target shipped with a demo pair; falls back to
    a pre/post difference heuristic for uploads and any pair missing labels.

    Pixel values match the xView2 scheme used by scoring.py:
        0 = background (no building)
        1 = none (undamaged building)
        2 = minor
        3 = major
        4 = destroyed
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    mask_path = out_dir / "damage_mask.png"

    target = resolve_demo_target(post_image_path)
    if target is not None:
        shutil.copy2(target, mask_path)
        return mask_path, "stub-groundtruth"

    return _diff_mask(pre_image_path, post_image_path, mask_path), "stub-heuristic"


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

    result = subprocess.run(command, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_SECONDS)

    if result.returncode != 0:
        raise RuntimeError(f"Docker baseline failed: {result.stderr or result.stdout}")

    mask_path = out_dir / f"{run_id}_mask.png"

    if not mask_path.exists():
        raise RuntimeError(f"Docker baseline did not produce mask: {mask_path}")

    return mask_path


def confidence_path_for_mask(mask_path: Path) -> Path:
    """Where infer_pair.py writes the per-pixel confidence map for a mask."""
    return mask_path.parent / f"{mask_path.stem}_confidence.npy"


def _run_pytorch_inference(
    pre_image_path: Path, post_image_path: Path, out_dir: Path
) -> tuple[Path, Path | None]:
    """Run the fine-tuned checkpoint via ml/pytorch-inference/infer_pair.py.

    Unlike the other two modes this one also yields a per-pixel confidence map,
    because the PyTorch model exposes class probabilities. The TF baseline and
    the stub emit label masks only.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = settings.pytorch_checkpoint_path
    if not checkpoint.exists():
        raise RuntimeError(
            f"PyTorch checkpoint not found: {checkpoint}. "
            "Train first (ml/finetune/run_amd_pipeline.sh) or set PYTORCH_CHECKPOINT_PATH."
        )

    infer_script = settings.pytorch_inference_dir / "infer_pair.py"
    if not infer_script.exists():
        raise RuntimeError(f"Missing inference script: {infer_script}")

    mask_path = out_dir / "damage_mask.png"
    command = [
        sys.executable,
        str(infer_script),
        "--pre",
        str(pre_image_path.resolve()),
        "--post",
        str(post_image_path.resolve()),
        "--checkpoint",
        str(checkpoint.resolve()),
        "--out",
        str(mask_path.resolve()),
    ]

    result = subprocess.run(
        command, capture_output=True, text=True, timeout=PYTORCH_TIMEOUT_SECONDS
    )

    if result.returncode != 0:
        raise RuntimeError(f"PyTorch inference failed: {result.stderr or result.stdout}")

    if not mask_path.exists():
        raise RuntimeError("PyTorch inference produced no output mask")

    confidence = confidence_path_for_mask(mask_path)
    return mask_path, confidence if confidence.exists() else None


def run_inference(
    pre_image_path: Path, post_image_path: Path, out_dir: Path
) -> tuple[Path, str, Path | None]:
    """Main inference entry point.

    main.py expects:
        mask_path, mode, confidence_path = run_inference(pre_path, post_path, out_dir)

    ``confidence_path`` is None for every mode except pytorch. Every failure
    surfaces as RuntimeError so callers can map inference outages to a 503
    rather than leaking a stack trace.
    """
    if settings.inference_mode == "stub":
        mask_path, mode = _make_stub_mask(pre_image_path, post_image_path, out_dir)
        return mask_path, mode, None

    if settings.inference_mode == "docker":
        try:
            mask_path = _run_docker_baseline(pre_image_path, post_image_path, out_dir)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            raise RuntimeError(f"Docker inference failed: {exc}") from exc
        return mask_path, "docker", None

    if settings.inference_mode == "pytorch":
        try:
            mask_path, confidence_path = _run_pytorch_inference(
                pre_image_path, post_image_path, out_dir
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            raise RuntimeError(f"PyTorch inference failed: {exc}") from exc
        return mask_path, "pytorch", confidence_path

    raise RuntimeError(f"Unsupported inference_mode: {settings.inference_mode}")