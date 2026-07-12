# Deploying DisasterIQ

Two free services: **backend on Render**, **frontend on Vercel**. Deploy the
backend first so you have its URL for the frontend.

> Note: real ML inference needs a GPU (added later), so the deployed backend runs
> in **stub mode**. That is not a placeholder for the demo pairs: each ships its
> xBD ground-truth damage mask, which stub mode serves directly (the API reports
> `stub-groundtruth`). Zone ranking, the overlay, live Fireworks AI briefs and
> PDF export are all real. What stub mode does *not* do is predict damage on
> imagery it has never seen — an uploaded pair with no ground truth falls back to
> a pre/post change-detection heuristic. See the inference-mode table in the
> [README](README.md#inference-modes).

---

## 1. Backend → Render

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **New → Blueprint**, select the `DarkNem4377/DisasterIQ` repo. Render reads
   [`render.yaml`](render.yaml) and configures the `disasteriq-backend` service.
3. Before the first deploy, open the service's **Environment** tab and set:
   - `FIREWORKS_API_KEY` = your Fireworks key (this is why it's `sync: false` —
     it is never committed).
4. Click **Deploy**. First build takes a few minutes.
5. Copy the service URL, e.g. `https://disasteriq-backend.onrender.com`.
6. Verify: open `https://<your-backend>.onrender.com/health` → should return
   `{"status":"ok","inference_mode":"stub",...}`.

> Free tier note: the service sleeps after ~15 min idle and takes ~30–60s to wake.
> The dashboard handles this — it shows a "Waking backend" state and keeps
> retrying until the backend answers, rather than reporting it as offline.

## 2. Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. **Add New → Project**, import the `DarkNem4377/DisasterIQ` repo.
3. Set **Root Directory** to `frontend`. Framework auto-detects as Next.js.
4. Add an **Environment Variable** (must be set before deploy — it's baked in at
   build time):
   - `NEXT_PUBLIC_API_URL` = your Render backend URL from step 1.5
     (e.g. `https://disasteriq-backend.onrender.com`)
5. Click **Deploy**. You'll get a URL like `https://disasteriq.vercel.app`.

## 3. Verify end-to-end

Open your Vercel URL, pick the demo pair, click **Analyze Damage**. You should
see the dashboard populate and a live AI brief (the backend CORS already allows
`*.vercel.app`). Put the Vercel URL in your GitHub repo's **About → Website**.

## Custom domain (optional)

Using a non-Vercel domain? Set `CORS_ORIGINS` in Render to a JSON list including
it, e.g. `["https://disasteriq.com"]`.
