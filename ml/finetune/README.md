# Fine-tuning on an AMD ROCm GPU

> **This does not fine-tune the TF 1.15 baseline.** TensorFlow 1.15 has no
> practical ROCm build, so there is no path from the Docker baseline weights to
> a fine-tuned model on AMD hardware. We fine-tune a PyTorch reimplementation
> (`michal2409/xView2`) instead and serve it via `INFERENCE_MODE=pytorch`. The
> TF baseline stays exactly as it is, for `INFERENCE_MODE=docker`.

## Prerequisites

1. Train archive verified and extracted to `data/train/`.
2. Subset filtered to the hazard types the demo shows:
   ```bash
   python scripts/prepare_train_subset.py --train-dir data/train --output-dir data/train_subset
   ```
3. An AMD GPU instance with ROCm, and a torch build that can see it:
   ```bash
   rocm-smi
   python -c "import torch; print(torch.cuda.is_available())"
   ```
4. Upstream cloned (gitignored — never committed):
   ```bash
   git clone https://github.com/michal2409/xView2 ml/pytorch-xview2
   ```

## One command

```bash
bash ml/finetune/run_amd_pipeline.sh
```

It patches upstream, regenerates `index.csv` for the subset, trains
localization, trains damage from the localization checkpoint, then evaluates.

## What each piece does

| File | Role |
|------|------|
| `config_subset.yaml` | Every hyperparameter. Nothing is hardcoded in the shell scripts. |
| `load_config.py` | Turns the YAML into `export` statements. Variables already set in the environment win, so `EPOCHS=1 bash train_damage.sh` works. |
| `patch_pytorch_xview2.py` | Ports the 2020 upstream to torch 2.x / PyTorch Lightning 1.9 / Python 3.11. Idempotent, and raises rather than silently no-opping if upstream moved. |
| `overrides/model/loss.py` | Upstream flattens damage pixels to `[N, C]`, which MONAI 1.x losses reject. Pure-PyTorch focal/dice on that path, MONAI on the spatial localization path. |
| `train_localization.sh` | Stage 1: segment buildings from the pre-disaster image. |
| `train_damage.sh` | Stage 2: siamese damage head, warm-started from stage 1. Refuses to run without that checkpoint. |
| `run_amd_pipeline.sh` | Both stages plus eval, in order. |

The pipeline is staged because the damage model initializes from the
localization weights (`ckpt_pre`). Training stage 2 from scratch runs fine and
quietly produces a much worse model, so `train_damage.sh` hard-fails instead.

Set `PYTHON=/path/to/python` if the image exposes `python` but not `python3`.

## Why the index has to be regenerated

The upstream loader maps a numeric `idx` to a tile by position in the sorted
image list, and ships an `index.csv` built against the full ~8k-pair train set.
Point it at a filtered subset without regenerating and it silently reads the
wrong tiles. `scripts/generate_subset_index.py` renumbers against whatever is
actually in `--data-dir`; `run_amd_pipeline.sh` calls it for you.

## Verify without a GPU

```bash
python ml/finetune/patch_pytorch_xview2.py --check    # do the patched files compile?
python -m pytest backend/tests/test_finetune_config.py -v
python -m pytest ml/pytorch-inference/tests/ -v
```

## After training

```bash
cp /results/dmg/checkpoints/best.ckpt ml/checkpoints/damage_best.ckpt
```

Then set `INFERENCE_MODE=pytorch` in `.env`. See [../checkpoints/README.md](../checkpoints/README.md).

If the GPU never materializes, ship with `INFERENCE_MODE=docker` — those
baseline weights are real, pretrained, and already working.
