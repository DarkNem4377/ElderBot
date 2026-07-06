# Fine-tuning on AMD GPU (Phase 3)

Run only after:
1. User says **"verify my downloads"** and train archive passes MD5 check
2. Train data extracted to `data/train/`
3. AMD Developer Cloud GPU credits are active

## Steps

```powershell
# 1. Extract train archive
tar -xzf D:\train_images_labels_targets.tar.gz -C D:\AMD\data

# 2. Filter to 3 hazard types
python scripts/prepare_train_subset.py --train-dir D:\AMD\data\train --output-dir D:\AMD\data\train_subset

# 3. On AMD cloud instance — verify ROCm
rocm-smi
python -c "import torch; print(torch.cuda.is_available())"

# 4. Split by disaster (baseline utils)
cd ml/xview2-baseline
python utils/split_into_disasters.py --input ../../data/train_subset --output ../../data/xbd_by_disaster

# 5. Follow upstream training pipeline in ml/xview2-baseline/README.md
#    - mask_polygons.py -> data_finalize.sh -> train_model.py (localization)
#    - process_data.py -> damage_classification.py (classification)

# 6. Point backend INFERENCE_MODE=docker at new weights or replace weights in baseline image
```

If train download completes too late for fine-tuning, ship with **baseline pretrained weights** (Unicorn track).
