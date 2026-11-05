# CycloneShield-Q

**CycloneShield-Q** is an agentic AI cyclone early-warning system with quantum-optimised evacuation routing, built for the IBM Hackathon by **Team Matrix Agents**.

It combines IBM watsonx Granite, Gemini, and Groq LLMs in a multi-agent pipeline, RAG-enhanced with historical cyclone data, quantum shelter optimisation via Qiskit QAOA, and a human-in-the-loop governance layer.

---

## Features

| Feature | Details |
|---|---|
| **Multi-agent pipeline** | WeatherTrack → Impact → QAOA → Evacuation → Human approval |
| **LLM fallback routing** | Granite (watsonx) → Gemini → Groq with automatic retry |
| **Quantum optimisation** | QAOA on Qiskit Aer selects optimal evacuation shelter |
| **RAG context** | ChromaDB + sentence-transformers for historical cyclone retrieval |
| **Interactive dashboard** | 4-page Streamlit UI with Plotly maps, gauges, and charts |
| **Governance & audit** | SQLite audit log, cost tracking, human approval gate |
| **Guardrails** | Regex-based input/output content checks |

---

## Dashboard Pages

### 🌩 Cyclone Detection
- Scenario presets (Odisha Cat-3, Andhra Cat-2, Gujarat Cat-1) + manual inputs
- Interactive OpenStreetMap with predicted track, cone of uncertainty, current position, landfall marker, impact-radius circle, and shelter pins
- Time slider to animate track hour by hour
- Wind-speed gauge with category colouring
- Wind & pressure dual-axis line chart
- District risk bar chart

### 🤖 Agent Pipeline
- Flow diagram (Weather → Impact → QAOA → Evacuation → Approval) with status colours
- **▶ Run Pipeline** button with progress bar
- Per-agent expandable cards: model used, tokens in/out, elapsed time, full markdown output

### ⚛ Quantum Optimiser
- Metric cards: QAOA vs Classical best shelter with Match/Differs badge
- QAOA circuit diagram (or text fallback)
- Bitstring probability histogram
- Objective value per shelter bar chart (chosen shelter highlighted)

### ✅ Approval & Logs
- SMS-style alert preview
- Evacuation plan markdown card with Approve / Reject buttons and approver name
- Audit log (newest first, 10 rows, no hash column)
- LLM cost total, per-agent table, cost-by-model pie chart

---

## Screenshots

> _Run the dashboard, take screenshots, and drop them into `docs/screenshots/` — update this section._

---

## Setup

### Requirements
- Python 3.12
- API keys for at least one provider: IBM watsonx, Google Gemini, or Groq

### Install

```bash
git clone https://github.com/BamboozleYou/IBMCycloneProject_MatrixAgents.git
cd IBMCycloneProject_MatrixAgents

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in your API keys
```

### Configure `.env`

```
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
WATSONX_URL=https://us-south.ml.cloud.ibm.com

GEMINI_API_KEY=...
GROQ_API_KEY=...
```

### Run

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

### Run a scenario from Python

```python
from agents.supervisor import Supervisor

sup = Supervisor()
results = sup.run({
    "name": "Fani-2",
    "category": 3,
    "landfall": "Odisha Coast",
    "wind_kmh": 185,
    "radius_km": 130,
    "pop_at_risk_k": 450,
})
print(results["evacuation_plan"])
```

---

## Project Structure

```
cycloneshield-q/
├── agents/          # WeatherTrack, Impact, Evacuation agents + BaseAgent
├── dashboard/       # Streamlit app (app.py)
├── gateway/         # LiteLLM router with Granite→Gemini→Groq fallback + cost log
├── governance/      # Audit log, policies
├── guardrails/      # Regex content checks
├── ingestion/       # Document loader for ChromaDB
├── memory/          # ChromaStore (RAG)
├── mcp/             # QAOA shelter optimiser (Qiskit)
├── observability/   # Structured logging
├── tests/           # pytest suite
└── requirements.txt
```

---

## License

MIT
