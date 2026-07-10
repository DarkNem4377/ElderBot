"""CPU-only tests for the probability -> (mask, confidence) conversion.

No GPU, no checkpoint, no upstream clone needed: these pin the numeric contract
that the backend's per-zone confidence depends on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infer_pair import confidence_path_for, probs_to_mask_and_confidence  # noqa: E402


def test_mask_is_argmax_and_confidence_is_the_winning_probability():
    probs = np.zeros((3, 4, 4), dtype=np.float32)
    probs[2, 0, 0] = 0.7
    probs[1, 0, 0] = 0.2
    probs[0, 0, 0] = 0.1

    probs[0, 1, 1] = 0.8
    probs[1, 1, 1] = 0.15
    probs[2, 1, 1] = 0.05

    mask, confidence = probs_to_mask_and_confidence(probs)

    assert mask[0, 0] == 2
    assert mask[1, 1] == 0
    assert confidence is not None
    assert confidence[0, 0] == pytest.approx(0.7)
    assert confidence[1, 1] == pytest.approx(0.8)
    assert np.allclose(confidence, probs.max(axis=0))


def test_confidence_is_not_softmaxed_a_second_time():
    """plt.py already applies softmax. Re-applying it deflates every value."""
    probs = np.array(
        [
            [[0.2, 0.5], [0.1, 0.25]],
            [[0.3, 0.3], [0.6, 0.25]],
            [[0.5, 0.2], [0.3, 0.50]],
        ],
        dtype=np.float32,
    )
    assert np.allclose(probs.sum(axis=0), 1.0), "fixture must be a valid distribution"

    _, confidence = probs_to_mask_and_confidence(probs)

    assert confidence is not None
    # A double softmax over [0.2,0.3,0.5] yields ~0.36, not 0.5.
    assert confidence[0, 0] == pytest.approx(0.5)
    assert np.all((confidence >= 0.0) & (confidence <= 1.0))


def test_ties_resolve_to_the_lowest_class_index():
    probs = np.full((3, 1, 1), 1 / 3, dtype=np.float32)
    mask, confidence = probs_to_mask_and_confidence(probs)
    assert mask[0, 0] == 0
    assert confidence[0, 0] == pytest.approx(1 / 3)


def test_label_output_yields_no_confidence():
    labels = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)
    mask, confidence = probs_to_mask_and_confidence(labels)
    assert confidence is None
    assert mask.shape == (2, 2)
    assert mask.dtype == np.uint8


def test_classes_are_clamped_to_the_xview2_range():
    labels = np.array([[-3.0, 9.0]], dtype=np.float32)
    mask, _ = probs_to_mask_and_confidence(labels)
    assert mask.tolist() == [[0, 4]]


def test_confidence_sidecar_path_matches_the_backend_contract():
    assert confidence_path_for(Path("/out/job/damage_mask.png")).name == (
        "damage_mask_confidence.npy"
    )
