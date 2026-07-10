# xView2 ML — DisasterIQ

Building damage assessment from paired pre/post satellite imagery.

## Framework decision

| Path | Framework | Status |
|------|-----------|--------|
| Demo inference (baseline) | TF 1.15 in Docker (`darknem-xview2-inference`) | Works today, ~2 min/pair on CPU |
| Fine-tuning | PyTorch + ROCm (`ml/pytorch-xview2`) | Needs an AMD GPU instance |
| Fine-tuning TF 1.15 on ROCm | — | **Rejected**: no practical ROCm build of TF 1.15 exists |

That last row is why fine-tuning runs against a PyTorch fork of xView2 rather
than the TF baseline we serve for the demo. Don't spend GPU hours rediscovering it.

## Inference modes

Set `INFERENCE_MODE` in `.env`. The backend validates the value at startup and
refuses to boot on a typo.

| Mode | Behavior | Confidence? | When |
|------|----------|-------------|------|
| `stub` | Copies the xBD ground-truth target when the pair ships one (`stub-groundtruth`), otherwise a pre/post pixel-difference heuristic (`stub-heuristic`) | no | Fast, dependency-free demo |
| `docker` | Official xView2 TF 1.15 baseline | no | Credibility, IoU baseline |
| `pytorch` | Fine-tuned checkpoint via `ml/pytorch-inference/` | **yes** | After GPU training |

**`stub-heuristic` cannot produce class 1 (undamaged building).** It only labels
*changed* pixels, as minor/major/destroyed. Undamaged buildings require ground
truth (`stub-groundtruth`) or a real model. Read demo numbers accordingly.

Only `pytorch` yields per-pixel class probabilities, so `zone.confidence` is
null in every other mode. The baseline and the stub emit label masks with no
probability behind them — reporting a number there would be inventing one.

## TF baseline inference image

Pretrained weights are downloaded during the image build:

- Localization: https://github.com/DIUx-xView/xView2/releases/download/v1.0/localization.h5
- Classification: https://github.com/DIUx-xView/xView2/releases/download/v1.0/classification.hdf5

### Build

```powershell
docker build -t darknem-xview2-inference -f ml/inference/Dockerfile ml/inference
# or
docker compose --profile build-ml build ml
```

Needs ~8 GB RAM and 15–30 minutes on a first build.

### Run the API against it

Use the local venv, **not** `docker compose up backend`: the backend image has
no Docker CLI inside it, so it cannot shell out to `docker run` per request.

```powershell
# .env
INFERENCE_MODE=docker

.\scripts\start-backend.ps1
```

### Test the container directly

```powershell
docker run --rm `
  -v ${PWD}\data\demo\images:/input:ro `
  -v ${PWD}\backend\outputs\smoke:/output `
  darknem-xview2-inference `
  /input/demo_pre_disaster.png `
  /input/demo_post_disaster.png `
  /output/localization.png `
  /output/classification.png
```

## PyTorch fine-tuning

Upstream (`michal2409/xView2`) is a gitignored clone, not vendored:

```bash
git clone https://github.com/michal2409/xView2 ml/pytorch-xview2
```

| Artifact | Path |
|----------|------|
| Upstream compatibility patches | `ml/finetune/patch_pytorch_xview2.py` |
| Loss override (MONAI 1.x) | `ml/finetune/overrides/model/loss.py` |
| Hyperparameters | `ml/finetune/config_subset.yaml` |
| Stage scripts | `ml/finetune/train_localization.sh`, `train_damage.sh` |
| Full pipeline | `ml/finetune/run_amd_pipeline.sh` |
| Single-pair inference | `ml/pytorch-inference/infer_pair.py` |
| Checkpoint destination | `ml/checkpoints/damage_best.ckpt` |

Details in [ml/finetune/README.md](finetune/README.md).

## Tests

The probability-to-confidence conversion is CPU-testable with no GPU, no
checkpoint and no upstream clone:

```bash
python -m pytest ml/pytorch-inference/tests/ -v
```
