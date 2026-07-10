# Merge Notes — DarkNem4377/DisasterIQ × AhmadRaza4076/DisasterIQ

Merged 2026-07-10. Base: DarkNem4377 (commit 2026-07-10 17:35). Overlay: AhmadRaza4076 (commit 2026-07-10 05:13).

## Component decisions

| Component | Taken from | Why |
|---|---|---|
| `backend/` (app + tests) | **DarkNem** | Strict superset of AR's backend: adds `security.py` (opt-in API token + per-IP rate limiting), typed `ReportRequest` (`AnalysisResult` instead of `dict`), Vercel CORS regex, degenerate-percentile handling + morphological opening in the stub mask, inference-mode normalization, `conftest.py`/`pytest.ini` for hermetic tests, and 21 more tests (incl. `test_security.py`, `test_narrator.py`). AR's backend logic is contained within it. |
| `frontend/` | **DarkNem** | Complete overhaul (1,019-line page vs 293), Logo/ZoneMapInner components, friendly error mapping, e2e clickthrough script, Next 15.5. AR's frontend is the pre-redesign version. |
| `ml/` (finetune, inference, checkpoints docs) | **AhmadRaza** | Contains the CUDA label-assert fix (target clamp + nearest-neighbor label downsample in `patch_pytorch_xview2.py`) that DarkNem's copy lacks, plus the full Kaggle pipeline (`kaggle_train.py`, resume script, smoke test, `overrides/main.py`). This tree is the one validated end-to-end against the trained checkpoint. |
| `data/demo/` | **AhmadRaza** | 10 real xView2 pairs with labels **and** ground-truth targets vs DarkNem's 2 unlabeled placeholder images. Labels enable geo enrichment; targets enable `stub-groundtruth` mode. |
| `notebooks/`, training `scripts/` | **AhmadRaza** | Kaggle/AMD training tooling (16 unique scripts). ML-pipeline scripts shared by both (`curate_demo_subset.ps1`, `generate_subset_index.py`, `prepare_train_subset.py`) taken from AR since they were exercised in AR's training run. |
| Dev `scripts/` (start-backend, verify-prerequisites, etc.) | **DarkNem** | `start-backend.ps1` launches from repo root so `config.py` finds `.env` — matches the merged backend's config semantics. |
| `docs/` | **Union** | DarkNem's setup docs (newer) + AR's six ML docs (AMD_CLOUD_SSH, AMD_FINETUNE_PLAN, DATA, DISK_SPACE, KAGGLE_FINETUNE, SUBMISSION). |
| CI (`.github/workflows/ci.yml`) | **DarkNem** | Same jobs; DN's drops redundant env vars (conftest handles them) and scopes triggers to main. AR's `test.yml` removed. |
| `docker-compose.yml` | **Merged** | DN base (docker.sock mount needed for docker inference mode) + AR's healthcheck, `restart: unless-stopped`, and health-gated `depends_on`. |
| `.gitignore` | **Merged union** | DN's comments + AR's training/staging/Kaggle ignores. |
| `.env.example`, `requirements*.txt` | **DarkNem** | Includes ACCESS_TOKEN/rate-limit docs; `anyio` pinned (imported directly in `main.py`). AR's unused `PYTORCH_DOCKER_IMAGE` setting dropped — nothing references it. |
| Fireworks model | **DarkNem** (`gpt-oss-120b`) | DN's narrator has reasoning-model handling (token budget, null-content fallback) tuned to it. |
| Deployment (`render.yaml`, `DEPLOY.md`), `LICENSE`, `NOTICE`, `Assets/`, root `README.md` | **DarkNem** | AR has no equivalents. README corrected: 10 demo pairs, not one. |
| `backend/tests/test_demo_coverage.py` | **AhmadRaza** (ported) | Regression-guards the curated 10-pair dataset's damage-class coverage. |
| `backend/tests/test_finetune_config.py` | **AhmadRaza** | Must assert AR's `ml/finetune/load_config.py` behavior (DN's version tests DN's diverged loader — 3 failures otherwise). |

## Verification (all on the merged tree)

- Backend: **77/77 pytest pass**.
- ML inference tests: **3/3 pass**, invoked from repo root exactly as CI does.
- Frontend: `tsc --noEmit` clean; `next build` clean (Next 15.5, static export of `/`).
- Live smoke: `/health` → 10 demo pairs; `/analyze` on `mexico-earthquake_00000005` → `stub-groundtruth`, `geo_available: true`, real centroids (19.326, −99.223); `/report/pdf` → valid 1-page PDF; `/brief` → stub fallback works without an API key; second pair (`midwest-flooding_00000008`) → top zone score 100.0.

## Flags

1. **`mexico-earthquake_00000005` scores 0.0 in every zone** — its ground-truth target contains only undamaged buildings, and scoring deliberately gives class-1 zero weight. Not a bug, but it's a dead demo pair for judging. Consider dropping it from the manifest or leading the demo with a flooding pair.
2. **No trained checkpoint in the repo** (by design — gitignored). `INFERENCE_MODE=pytorch` requires `ml/checkpoints/damage_best.ckpt` from the AMD/Kaggle run. Stub and docker modes verified; pytorch mode untestable here.
3. **Docker inference mode — smoke-tested and verified 2026-07-11.** Built the `darknem-xview2-inference` image locally and ran `midwest-flooding_00000008` through both the raw container (exit 0, mask with damage classes 0/1/2/4) and the full backend path (`INFERENCE_MODE=docker` → `POST /analyze` → HTTP 200 in ~137s, `geo_available: true`, 8 zones, top zone priority 100.0). The `run.sh` arg contract works as-is. Note: first analyze is slow (~2 min TF-1.15 cold start + two models), so `stub` remains the sensible default for a live demo.
