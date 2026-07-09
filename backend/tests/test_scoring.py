from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from app.schemas import BuildingCounts
from app.services.scoring import (
    building_counts_for_region,
    counts_for_region,
    priority_score,
    score_mask,
)


def test_counts_for_region_basic():
    mask = np.array(
        [
            [0, 1, 1],
            [2, 2, 3],
            [4, 4, 4],
        ],
        dtype=np.uint8,
    )
    counts = counts_for_region(mask)
    assert counts.none == 2
    assert counts.minor == 2
    assert counts.major == 1
    assert counts.destroyed == 3


def test_building_counts_for_region_single_component():
    mask = np.zeros((6, 6), dtype=np.uint8)
    mask[1:4, 1:4] = 2  # one contiguous "minor" blob
    counts = building_counts_for_region(mask)
    assert counts.minor == 1
    assert counts.none == 0
    assert counts.major == 0
    assert counts.destroyed == 0


def test_building_counts_for_region_multiple_components():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[0:2, 0:2] = 3  # major blob #1
    mask[7:9, 7:9] = 3  # major blob #2, disconnected
    counts = building_counts_for_region(mask)
    assert counts.major == 2


def test_priority_score_weighting():
    mostly_destroyed = BuildingCounts(none=0, minor=0, major=0, destroyed=10)
    mostly_undamaged = BuildingCounts(none=10, minor=0, major=0, destroyed=0)
    assert priority_score(mostly_destroyed) > priority_score(mostly_undamaged)


def test_priority_score_empty():
    assert priority_score(BuildingCounts()) == 0.0


def test_score_mask_end_to_end(tmp_path):
    mask = np.zeros((40, 40), dtype=np.uint8)
    mask[2:10, 2:10] = 2  # minor buildings, top-left grid cell
    mask[30:38, 30:38] = 4  # destroyed buildings, bottom-right grid cell

    mask_path = tmp_path / "mask.png"
    Image.fromarray(mask).save(mask_path)

    result = score_mask(mask_path, grid_rows=4, grid_cols=4)

    assert result.summary.total_buildings == 2
    assert result.summary.destroyed_pct == pytest.approx(50.0)

    ranks = [zone.rank for zone in result.zones]
    assert ranks == sorted(ranks)
    assert result.zones[0].priority_score >= result.zones[-1].priority_score
    assert result.zones[0].building_counts.destroyed == 1
