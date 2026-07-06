"""Deterministic zone scoring from xView2 damage masks (pixel values 0-4)."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image

from app.schemas import AnalysisResult, AnalysisSummary, DamageCounts, Zone

# xView2 class pixel values
CLASS_NAMES = {
    0: "background",
    1: "none",
    2: "minor",
    3: "major",
    4: "destroyed",
}

# Overlay colors (RGBA) for frontend legend
OVERLAY_COLORS = {
    0: (0, 0, 0, 0),
    1: (34, 197, 94, 120),    # green - no damage
    2: (59, 130, 246, 140),   # blue - minor
    3: (249, 115, 22, 160),   # orange - major
    4: (239, 68, 68, 180),    # red - destroyed
}

WEIGHTS = {1: 1.0, 2: 2.0, 3: 3.5, 4: 5.0}


def load_mask(path: Path) -> np.ndarray:
    with Image.open(path) as img:
        return np.array(img.convert("L"), dtype=np.uint8)


def counts_for_region(mask: np.ndarray) -> DamageCounts:
    building = mask > 0
    if not building.any():
        return DamageCounts()
    vals, cnts = np.unique(mask[building], return_counts=True)
    mapping = dict(zip(vals.tolist(), cnts.tolist()))
    return DamageCounts(
        none=int(mapping.get(1, 0)),
        minor=int(mapping.get(2, 0)),
        major=int(mapping.get(3, 0)),
        destroyed=int(mapping.get(4, 0)),
    )


def priority_score(counts: DamageCounts) -> float:
    total = counts.none + counts.minor + counts.major + counts.destroyed
    if total == 0:
        return 0.0
    weighted = (
        counts.none * WEIGHTS[1]
        + counts.minor * WEIGHTS[2]
        + counts.major * WEIGHTS[3]
        + counts.destroyed * WEIGHTS[4]
    )
    return round((weighted / total) * 100, 2)


def score_mask(mask_path: Path, grid_rows: int = 4, grid_cols: int = 4) -> AnalysisResult:
    mask = load_mask(mask_path)
    h, w = mask.shape
    cell_h = max(1, h // grid_rows)
    cell_w = max(1, w // grid_cols)

    zones: list[Zone] = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            y0 = row * cell_h
            x0 = col * cell_w
            y1 = h if row == grid_rows - 1 else (row + 1) * cell_h
            x1 = w if col == grid_cols - 1 else (col + 1) * cell_w
            region = mask[y0:y1, x0:x1]
            counts = counts_for_region(region)
            total_building = counts.none + counts.minor + counts.major + counts.destroyed
            if total_building == 0:
                continue
            zones.append(
                Zone(
                    rank=0,
                    bbox=[int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
                    damage_counts=counts,
                    priority_score=priority_score(counts),
                )
            )

    zones.sort(key=lambda z: z.priority_score, reverse=True)
    for i, zone in enumerate(zones, start=1):
        zone.rank = i

    all_counts = counts_for_region(mask)
    total_building = (
        all_counts.none + all_counts.minor + all_counts.major + all_counts.destroyed
    )
    summary = AnalysisSummary(
        total_building_pixels=total_building,
        destroyed_pct=round(all_counts.destroyed / total_building * 100, 2) if total_building else 0.0,
        major_pct=round(all_counts.major / total_building * 100, 2) if total_building else 0.0,
        minor_pct=round(all_counts.minor / total_building * 100, 2) if total_building else 0.0,
    )

    overlay = _build_overlay(mask)
    buf = io.BytesIO()
    overlay.save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return AnalysisResult(
        zones=zones,
        summary=summary,
        mask_path=str(mask_path),
        mask_base64=mask_b64,
        inference_mode="scoring",
    )


def _build_overlay(mask: np.ndarray) -> Image.Image:
    h, w = mask.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    for cls, color in OVERLAY_COLORS.items():
        if cls == 0:
            continue
        rgba[mask == cls] = color
    return Image.fromarray(rgba, mode="RGBA")
