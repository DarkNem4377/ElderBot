#!/usr/bin/env bash
# Full fine-tune on an AMD ROCm GPU instance: patch -> index -> loc -> dmg -> eval.
#
# Prerequisites:
#   git clone https://github.com/michal2409/xView2 ml/pytorch-xview2
#   host data mounted at /data, results at /results
set -euo pipefail

# ROCm and Kaggle images disagree on whether the interpreter is python3 or python.
PYTHON="${PYTHON:-python3}"

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FINETUNE_DIR="$REPO_ROOT/ml/finetune"
XVIEW2_ROOT="$REPO_ROOT/ml/pytorch-xview2"

echo "=== ROCm GPU check ==="
rocm-smi || echo "WARN: rocm-smi unavailable"
"$PYTHON" - <<'PY' || echo "WARN: torch not importable"
import torch
print("gpu visible:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY

if [[ ! -d "$XVIEW2_ROOT" ]]; then
  echo "error: missing $XVIEW2_ROOT" >&2
  echo "       git clone https://github.com/michal2409/xView2 ml/pytorch-xview2" >&2
  exit 1
fi

echo "=== Patch upstream for modern torch / PyTorch Lightning ==="
"$PYTHON" "$FINETUNE_DIR/patch_pytorch_xview2.py"

eval "$("$PYTHON" "$FINETUNE_DIR/load_config.py" data)"

# The loader indexes tiles by position in the sorted image list, so the index
# must be regenerated for the subset — the full-train index would mis-address.
INDEX_CSV="$XVIEW2_ROOT/utils/index.csv"
export XVIEW2_INDEX_CSV="$INDEX_CSV"

echo "=== Generate index.csv for $DATA_DIR ==="
"$PYTHON" "$REPO_ROOT/scripts/generate_subset_index.py" --data-dir "$DATA_DIR" --out "$INDEX_CSV"

mkdir -p "$RESULTS_ROOT"

echo "=== Stage 1: localization ==="
RESULTS_DIR="$RESULTS_ROOT/loc" bash "$FINETUNE_DIR/train_localization.sh"

echo "=== Stage 2: damage ==="
RESULTS_DIR="$RESULTS_ROOT/dmg" CKPT_PRE="$RESULTS_ROOT/loc/checkpoints/best.ckpt" \
  bash "$FINETUNE_DIR/train_damage.sh"

echo "=== Eval on held-out test set ==="
cd "$XVIEW2_ROOT"
"$PYTHON" main.py \
  --exec_mode eval \
  --type post \
  --ckpt "$RESULTS_ROOT/dmg/checkpoints/best.ckpt" \
  --data "$TEST_DIR" \
  --results "$RESULTS_ROOT/eval" \
  --gpus 1 \
  --val_batch_size 4

echo
echo "Done. Copy the checkpoint back to the app:"
echo "  cp $RESULTS_ROOT/dmg/checkpoints/best.ckpt $REPO_ROOT/ml/checkpoints/damage_best.ckpt"
echo "  # then set INFERENCE_MODE=pytorch in .env"
ls -la "$RESULTS_ROOT/dmg/checkpoints/" || true
