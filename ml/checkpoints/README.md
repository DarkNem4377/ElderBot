# Fine-tuned checkpoints

Checkpoints are **gitignored** — they are hundreds of megabytes and regenerable.

After training finishes on the GPU box, copy the damage checkpoint here:

```bash
cp /results/dmg/checkpoints/best.ckpt ml/checkpoints/damage_best.ckpt
```

Then point the backend at it:

```ini
# .env
INFERENCE_MODE=pytorch
PYTORCH_CHECKPOINT_PATH=ml/checkpoints/damage_best.ckpt
```

The path is relative to the repo root, so it resolves the same whether uvicorn
starts from the root or from `backend/`. `/analyze` will return 503 with a clear
message if the checkpoint is missing, rather than falling back to the stub —
silently serving fake damage from a "pytorch" deployment would be worse.
