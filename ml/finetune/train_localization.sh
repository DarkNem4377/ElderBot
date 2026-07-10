#!/usr/bin/env bash
# Stage 1: learn building segmentation from pre-disaster imagery.
# Hyperparameters come from config_subset.yaml; any exported env var wins.
set -euo pipefail

# ROCm and Kaggle images disagree on whether the interpreter is python3 or python.
PYTHON="${PYTHON:-python3}"

FINETUNE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XVIEW2_ROOT="${XVIEW2_ROOT:-$FINETUNE_DIR/../pytorch-xview2}"

if [[ ! -f "$XVIEW2_ROOT/main.py" ]]; then
  echo "error: no xView2 checkout at $XVIEW2_ROOT" >&2
  echo "       git clone https://github.com/michal2409/xView2 ml/pytorch-xview2" >&2
  exit 1
fi

eval "$("$PYTHON" "$FINETUNE_DIR/load_config.py" localization)"
eval "$("$PYTHON" "$FINETUNE_DIR/load_config.py" data)"

RESULTS_DIR="${RESULTS_DIR:?load_config must export RESULTS_DIR}"
mkdir -p "$RESULTS_DIR"

cd "$XVIEW2_ROOT"
exec "$PYTHON" main.py \
  --exec_mode train \
  --type pre \
  --encoder "$ENCODER" \
  --loss_str "$LOSS_STR" \
  --epochs "$EPOCHS" \
  --batch_size "$BATCH_SIZE" \
  --val_batch_size "$VAL_BATCH_SIZE" \
  --gpus "$GPUS" \
  --data "$DATA_DIR" \
  --results "$RESULTS_DIR"
