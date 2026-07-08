<p align="center">
  <img src="./Assets/DisasterIQ-logo.png" alt="DisasterIQ-logo.png" width="350">
</p>

<h1 align="center"> DisasterIQ</h1>

<p align="center">
  <strong>SEE DAMAGE. PRIORITIZE RELIEF. SAVE LIVES..</strong>
</p>

````markdown
# 🌍 DisasterIQ

### AI-Powered Satellite Disaster-Damage Triage System  
**See damage. Prioritize relief. Save lives.**

---

## 🚨 Problem

When floods, earthquakes, wildfires, or hurricanes strike, emergency teams need to know **where damage is worst first**.

Current disaster assessment is often slow, manual, dangerous, and incomplete. Relief teams may spend days waiting for ground surveys while affected communities need help immediately.

**DisasterIQ** helps turn before/after disaster imagery into fast, visual, actionable response intelligence.

---

## 🧠 What DisasterIQ Does

DisasterIQ is a disaster intelligence dashboard that:

- 🛰️ Accepts before/after satellite or aerial imagery
- 🏚️ Detects and estimates building damage severity
- 🎨 Displays a color-coded damage overlay
- 📊 Summarizes damage by severity level
- 📍 Ranks priority response zones
- 🧾 Generates an emergency situation brief
- 📄 Exports a field-ready damage report
- ⚡ Supports an AMD + ROCm accelerated AI workflow

---

## 🎯 Damage Classes

| Class | Meaning |
|---|---|
| 🟢 No Damage | Structure appears intact |
| 🟡 Minor Damage | Light visible damage |
| 🟠 Major Damage | Serious visible damage |
| 🔴 Destroyed | Severe destruction or likely collapse |

---

## 🖥️ Demo Flow

```text
Load Demo Pair
      ↓
Display Before / After Imagery
      ↓
Analyze Damage
      ↓
Render Damage Overlay
      ↓
Generate Damage Summary
      ↓
Rank Priority Zones
      ↓
Generate Situation Brief
      ↓
Export Field Report PDF
````

---

## 🌐 Global Disaster Use Case

DisasterIQ is designed for **global disaster imagery**, not only one country.

The demo can be adapted for different disaster scenarios as long as a usable before/after image pair is available.

Example use cases:

* 🇵🇰 Pakistan floods
* 🇻🇪 Venezuela earthquakes
* 🇹🇷 Turkey/Syria earthquakes
* 🇺🇸 Hurricanes and wildfires
* 🇯🇵 Earthquakes and tsunamis
* 🌍 Any region with before/after satellite or aerial imagery

---

## 🧩 Tech Stack

### Frontend

* ⚛️ Next.js
* 🟦 TypeScript
* 🎨 Tailwind CSS
* 🖼️ Image comparison dashboard
* 📊 Damage summary and priority zone UI

### Backend

* 🐍 Python
* ⚡ FastAPI
* 🖼️ Image processing pipeline
* 📡 REST API
* 📄 PDF report generation

### AI / ML

* 🔥 PyTorch
* ⚙️ ROCm-compatible inference path
* 🧠 Damage classification pipeline
* 📊 Priority zone scoring
* 🤖 Fireworks AI support for situation brief generation

### AMD Stack

* 🚀 AMD Instinct GPU target
* ⚙️ ROCm compute stack
* 🔥 PyTorch on ROCm
* 🤖 Fireworks AI hosted model support

---

## 🏗️ Architecture

```text
Browser / Next.js Frontend
        │
        ▼
FastAPI Backend
        │
        ├── Demo Pair Loading
        ├── Image Upload Handling
        ├── Damage Inference Pipeline
        ├── Zone Priority Scoring
        ├── Situation Brief Generation
        └── PDF Report Export
        │
        ▼
AMD / ROCm / PyTorch Inference Path
```

---

## 🔌 API Overview

| Endpoint                  | Method | Purpose                          |
| ------------------------- | ------ | -------------------------------- |
| `/health`                 | GET    | Check backend health             |
| `/demo/pairs`             | GET    | List available demo image pairs  |
| `/demo/images/{filename}` | GET    | Serve demo images                |
| `/analyze`                | POST   | Run damage analysis              |
| `/brief`                  | POST   | Generate situation brief         |
| `/analyze-and-brief`      | POST   | Run full analysis and brief flow |

---

## 📊 Example Output

```json
{
  "summary": {
    "total_building_pixels": 16,
    "destroyed_pct": 50.0,
    "major_pct": 25.0,
    "minor_pct": 25.0
  },
  "zones": [
    {
      "rank": 1,
      "priority_score": 500,
      "damage_counts": {
        "destroyed": 1,
        "major": 0,
        "minor": 0,
        "none": 0
      }
    }
  ],
  "inference_mode": "stub"
}
```

---

## 🧾 Situation Brief Example

```text
SITUATION BRIEF

Context:
Disaster response teams should prioritize areas with the highest concentration of destroyed and major-damage structures.

Overall:
16 buildings assessed.
Destroyed: 50%
Major Damage: 25%
Minor Damage: 25%

Recommendation:
Deploy assessment teams to the highest-scored zones first while verifying access routes and secondary hazards.
```

---

## 📄 PDF Report Export

DisasterIQ can export a field damage report containing:

* 🧾 Disaster pair ID
* ⚙️ Inference mode
* 📊 Damage summary
* 📍 Ranked priority zones
* 🧠 Situation brief
* 🚧 Field coordination notes

---

## ✅ Current Status

### Working

* ✅ Frontend dashboard
* ✅ Backend API
* ✅ Demo pair loading
* ✅ Before/after image rendering
* ✅ Damage analysis button flow
* ✅ Damage summary cards
* ✅ Priority zone ranking
* ✅ Situation brief panel
* ✅ PDF report export
* ✅ Frontend/backend integration

### In Progress

* 🚧 Real trained model integration
* 🚧 ROCm benchmark capture
* 🚧 Fireworks AI live narration
* 🚧 Docker Compose finalization
* 🚧 Demo video recording
* 🚧 Final README screenshots

---

## ⚠️ Development Note

The current demo may run in **stub inference mode** depending on local configuration.

Stub mode is useful for testing the full product workflow:

```text
image pair → analysis → overlay → zones → brief → PDF
```

Final accuracy and benchmark claims should only be made after verified model inference and real AMD/ROCm benchmark capture.

---

## 🚀 Running Locally

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

## 🧪 How to Test

1. Start the backend on port `8000`
2. Start the frontend on port `3000`
3. Open the dashboard
4. Click **Load Demo Pair**
5. Confirm before/after images appear
6. Click **Analyze Damage**
7. Review:

   * Damage overlay
   * Damage summary
   * Priority zones
   * Situation brief
   * PDF report export

---

## 🐳 Docker

Docker support is planned for final deployment.

Target command:

```bash
docker compose up --build
```

---

## 📈 Benchmarks

Final benchmark table will include:

| Metric                | CPU | AMD GPU / ROCm |
| --------------------- | --: | -------------: |
| Inference latency     | TBD |            TBD |
| Buildings/sec         | TBD |            TBD |
| End-to-end scene time | TBD |            TBD |
| Model confidence      | TBD |            TBD |

Benchmark numbers should come from real captured runs.

---

## 🏆 Hackathon Context

DisasterIQ was built for the:

**AMD Developer Hackathon: ACT II — Unicorn Track**

Judging alignment:

| Criteria                      | DisasterIQ Alignment                                                         |
| ----------------------------- | ---------------------------------------------------------------------------- |
| 🎨 Creativity & Originality   | Disaster-response AI using before/after imagery                              |
| 📈 Product / Market Potential | Useful for emergency teams, NGOs, relief agencies, and disaster coordinators |
| ✅ Completeness                | Full demo flow from imagery to report export                                 |
| ⚡ AMD Platform Usage          | Designed around AMD Instinct, ROCm, PyTorch, and Fireworks AI                |

---

## 🧠 Why This Matters

In a disaster, hours matter.

DisasterIQ helps emergency teams quickly answer:

* Where is the damage worst?
* Which zones need inspection first?
* How many structures appear severely affected?
* Where should limited rescue resources go first?
* What should field teams know before entering the area?

DisasterIQ is not a replacement for ground truth verification. It is a decision-support layer designed to help response teams move faster.

---

## 👥 Team

Built by **Team DarkNem**

---

## ⚠️ Disclaimer

DisasterIQ is a hackathon prototype.

It should not be used as the sole basis for real-world emergency decisions. AI-generated outputs must be verified by qualified disaster-response professionals, satellite imagery analysts, and field teams before operational use.

---

## 📜 License

License TBD.

---

## 🌟 Final Message

**DisasterIQ turns disaster imagery into actionable response intelligence.**

.

```
```
