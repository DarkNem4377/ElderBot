"""Emit shell `export` statements from ml/finetune/config_subset.yaml.

Keeps the training shell scripts free of hardcoded hyperparameters:

    eval "$(python ml/finetune/load_config.py localization)"
    eval "$(python ml/finetune/load_config.py damage)"
    eval "$(python ml/finetune/load_config.py data)"

Values already present in the environment win, so a caller can override a
single knob (``EPOCHS=1 bash train_damage.sh``) without editing the YAML.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - dependency hint only
    print("pyyaml is required: pip install pyyaml", file=sys.stderr)
    raise

DEFAULT_CONFIG = Path(__file__).resolve().parent / "config_subset.yaml"

SECTION_KEYS = {
    "localization": {
        "EPOCHS": "epochs",
        "BATCH_SIZE": "batch_size",
        "VAL_BATCH_SIZE": "val_batch_size",
        "ENCODER": "encoder",
        "LOSS_STR": "loss_str",
        "GPUS": "gpus",
        "RESULTS_DIR": "results_dir",
    },
    "damage": {
        "EPOCHS": "epochs",
        "BATCH_SIZE": "batch_size",
        "VAL_BATCH_SIZE": "val_batch_size",
        "ENCODER": "encoder",
        "LOSS_STR": "loss_str",
        "DMG_MODEL": "dmg_model",
        "GPUS": "gpus",
        "RESULTS_DIR": "results_dir",
        "CKPT_PRE": "ckpt_pre",
    },
}

DATA_KEYS = {
    "DATA_DIR": ("train_dir", "/data/train_subset"),
    "TEST_DIR": ("test_dir", "/data/test"),
    "RESULTS_ROOT": ("results_root", "/results"),
}


def resolve_config(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    return Path(os.environ.get("FINETUNE_CONFIG") or DEFAULT_CONFIG)


def _emit(env_key: str, value: object) -> None:
    """Print one export, quoted so paths with spaces survive `eval`."""
    print(f"export {env_key}={shlex.quote(str(value))}")


def emit_section(cfg: dict, section: str) -> None:
    if section == "data":
        data = cfg.get("data", {})
        for env_key, (yaml_key, fallback) in DATA_KEYS.items():
            # A non-empty environment variable is an explicit caller override.
            if os.environ.get(env_key):
                continue
            _emit(env_key, data.get(yaml_key, fallback))
        return

    values = cfg.get(section, {})
    for env_key, yaml_key in SECTION_KEYS[section].items():
        value = values.get(yaml_key)
        if value is None:
            continue
        if os.environ.get(env_key):
            continue
        _emit(env_key, value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section", choices=["localization", "damage", "data"])
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    config_path = resolve_config(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    emit_section(cfg, args.section)


if __name__ == "__main__":
    main()
