"""The training shell scripts consume these exports, so their shape is a contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LOAD_CONFIG = REPO_ROOT / "ml" / "finetune" / "load_config.py"

pytest.importorskip("yaml", reason="pyyaml is a dev-only dependency")


def _run(section: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        [sys.executable, str(LOAD_CONFIG), section],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout


def _parse(stdout: str) -> dict[str, str]:
    exports = {}
    for line in stdout.strip().splitlines():
        key, _, value = line.removeprefix("export ").partition("=")
        exports[key] = value.strip("'\"")
    return exports


def test_localization_exports_training_hyperparameters():
    exports = _parse(_run("localization"))
    assert exports["EPOCHS"] == "10"
    assert exports["BATCH_SIZE"] == "8"
    assert exports["ENCODER"] == "resnet50"
    assert exports["LOSS_STR"] == "ce+dice"


def test_damage_stage_chains_to_the_localization_checkpoint():
    """Stage 2 must start from stage 1's weights, not from scratch."""
    localization = _parse(_run("localization"))
    damage = _parse(_run("damage"))

    assert damage["CKPT_PRE"].startswith(localization["RESULTS_DIR"])
    assert damage["DMG_MODEL"] == "siamese"
    assert damage["LOSS_STR"] == "focal+dice"


def test_data_section_exports_every_path_the_pipeline_needs():
    exports = _parse(_run("data"))
    assert set(exports) == {"DATA_DIR", "TEST_DIR", "RESULTS_ROOT"}


def test_environment_overrides_win_over_the_yaml():
    import os

    env = {**os.environ, "EPOCHS": "1"}
    exports = _parse(_run("damage", env=env))
    assert "EPOCHS" not in exports, "an explicit override must not be clobbered by the config"


def test_data_paths_also_honour_overrides():
    """run_amd_pipeline.sh exports DATA_DIR before the train scripts re-read it."""
    import os

    env = {**os.environ, "DATA_DIR": "/mnt/scratch/subset"}
    exports = _parse(_run("data", env=env))
    assert "DATA_DIR" not in exports
    assert exports["TEST_DIR"] == "/data/test"
