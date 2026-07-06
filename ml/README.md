# xView2 Baseline (vendored)

Official localization + classification pipeline for building damage assessment.

## Weights

Pretrained weights are downloaded when building the Docker image:

- Localization: https://github.com/DIUx-xView/xView2/releases/download/v1.0/localization.h5
- Classification: https://github.com/DIUx-xView/xView2/releases/download/v1.0/classification.hdf5

## Build inference image

```powershell
cd submission
docker build -t darknem-xview2-inference .
```

Requires ~8GB RAM and network access during build.

## Manual inference

See upstream README: `utils/inference.sh`
