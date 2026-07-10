#!/usr/bin/env bash
# Stage 2: siamese damage classifier over (pre, post), warm-started from stage 1.
# Fails fast if the localization checkpoint is absent — training from scratch
# here silently produces a much worse model rather than an error.
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

eval "$("$PYTHON" "$FINETUNE_DIR/load_config.py" damage)"
eval "$("$PYTHON" "$FINETUNE_DIR/load_config.py" data)"

RESULTS_DIR="${RESULTS_DIR:?load_config must export RESULTS_DIR}"
CKPT_PRE="${CKPT_PRE:?load_config must export CKPT_PRE}"

if [[ ! -f "$CKPT_PRE" ]]; then
  echo "error: localization checkpoint not found: $CKPT_PRE" >&2
  echo "       run train_localization.sh first." >&2
  exit 1
fi

mkdir -p "$RESULTS_DIR"

cd "$XVIEW2_ROOT"
exec "$PYTHON" main.py \
  --exec_mode train \
  --type post \
  --dmg_model "$DMG_MODEL" \
  --encoder "$ENCODER" \
  --loss_str "$LOSS_STR" \
  --epochs "$EPOCHS" \
  --batch_size "$BATCH_SIZE" \
  --val_batch_size "$VAL_BATCH_SIZE" \
  --gpus "$GPUS" \
  --data "$DATA_DIR" \
  --results "$RESULTS_DIR" \
  --ckpt_pre "$CKPT_PRE"
