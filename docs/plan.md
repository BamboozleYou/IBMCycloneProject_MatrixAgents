# CycloneShield Q — Minimal Prototype Plan
**Team Matrix Agents:** Vamika A Bhat · Aanand Krishnan
**Hackathon:** Edunet × IBM SkillsBuild, Bengaluru 2026

> **Scope:** Smallest possible implementation that satisfies all 16 mentor steps. Every component below maps to at least one step. Nothing extra.

---

## Mentor-Step Coverage Map

| Step | Covered by |
|---|---|
| 1 Problem & Requirements | This plan + README |
| 2 Architecture & Stack | `docs/plan.md`, `README.md` |
| 3 IBM Bob dev environment | Bob session (Plan → Agent mode) |
| 4 Data source integration | `data/seed_cyclones.json` (5 historical notes) + Open-Meteo stub |
| 5 Specialised agents (≥3) | `agents/weather_track.py` · `agents/impact.py` · `agents/evacuation.py` |
| 6 Multi-agent orchestration | `agents/supervisor.py` (sequential dispatch) |
| 7 Multi-LLM + fallback | `gateway/litellm_router.py` (Granite 4 → Gemini → Groq fallback) |
| 8 MCP tool integration | `mcp/qaoa_shelter.py` (Qiskit QAOA vs brute-force) |
| 9 Memory + vector DB | `memory/chroma_store.py` (ChromaDB, 5 seeded notes, RAG retrieval) |
| 10 LLM gateway + cost log | `gateway/litellm_router.py` + `gateway/cost_log.py` (SQLite) |
| 11 Observability | `observability/logger.py` (structured JSON log, per-agent timing) |
| 12 Guardrails + HITL | `guardrails/regex_guard.py` + approval button in dashboard |
| 13 Governance + audit log | `governance/policies.yaml` + `governance/audit.py` (SQLite) |
| 14 Dashboard | `dashboard/app.py` — 3 pages (Command Center, Alert Center, Gateway) |
| 15 Tests | `tests/test_agents.py` · `tests/test_qaoa.py` · `tests/test_rag.py` |
| 16 Docker + deployment | `Dockerfile` + `README.md` deploy section |

---

## File Structure

```
cycloneshield-q/
├── .env.example               # Key names only (never commit values)
├── .gitignore
├── README.md
├── Dockerfile
├── requirements.txt
│
├── docs/
│   └── plan.md                # ← this file
│
├── data/
│   └── seed_cyclones.json     # 5 past-cyclone records for ChromaDB seed
│
├── agents/
│   ├── base_agent.py          # Shared BaseAgent(name, llm_model, system_prompt)
│   ├── weather_track.py       # WeatherTrackAgent → Granite 4 via LiteLLM
│   ├── impact.py              # ImpactAgent → Gemini via LiteLLM
│   ├── evacuation.py          # EvacuationAgent → Groq via LiteLLM
│   └── supervisor.py          # Supervisor: sequential dispatch + HITL gate
│
├── mcp/
│   └── qaoa_shelter.py        # MCP tool: QAOA shelter optimiser (Qiskit Aer sim)
│                              #           + brute-force fallback; returns JSON
│
├── memory/
│   └── chroma_store.py        # ChromaDB client; seed() + retrieve(query, k=2)
│
├── gateway/
│   ├── litellm_router.py      # LiteLLM completion() with fallback list; wraps call
│   └── cost_log.py            # SQLite table: (ts, agent, model, tokens_in, tokens_out, usd)
│
├── guardrails/
│   └── regex_guard.py         # check_input(text) / check_output(text) → raises GuardError
│
├── governance/
│   ├── policies.yaml          # Allowed models per agent, max_tokens, require_approval flags
│   └── audit.py               # SQLite table: (ts, agent, action, approved_by, payload_hash)
│
├── observability/
│   └── logger.py              # structlog JSON logger; log_call(agent, duration_ms, status)
│
├── dashboard/
│   └── app.py                 # Streamlit 3-page app (st.sidebar radio)
│                              #   Page 1 — Command Center: run pipeline, agent status
│                              #   Page 2 — Alert Center: last alert, HITL approve button
│                              #   Page 3 — Gateway: token/cost table from SQLite
│
└── tests/
    ├── test_agents.py          # Patch LiteLLM; assert each agent returns non-empty string
    ├── test_qaoa.py            # Assert QAOA result ≥ brute-force objective (or equal)
    └── test_rag.py             # Seed ChromaDB; assert retrieve() returns ≥1 document
```

---

## Sub-Tasks

### ST-1 — Scaffold & Config
**Intent:** Create skeleton files, `.env.example`, `.gitignore`, `requirements.txt` so every subsequent sub-task has a clean starting point.

**Expected Outcomes:**
- Repo imports without error (`python -c "import agents, gateway, mcp, memory, guardrails, governance, observability"`)
- `requirements.txt` pins: `litellm`, `qiskit`, `qiskit-aer`, `chromadb`, `sentence-transformers`, `streamlit`, `structlog`, `pyyaml`, `pytest`

**Todo List:**
- [ ] Create all `__init__.py` stubs
- [ ] Write `requirements.txt` with pinned versions
- [ ] Write `.env.example` (WATSONX_API_KEY, WATSONX_URL, GEMINI_API_KEY, GROQ_API_KEY)
- [ ] Write `.gitignore` (`.env`, `chroma_db/`, `.venv/`, `__pycache__/`, `*.db`)

**Status:** [ ] pending

---

### ST-2 — Data Seed (5 Past-Cyclone Notes)
**Intent:** Provide the 5 historical cyclone records that seed ChromaDB and serve as static demo data throughout the prototype.

**Expected Outcomes:**
- `data/seed_cyclones.json` exists with 5 objects each having `id`, `name`, `year`, `category`, `landfall_region`, `summary` fields
- `memory/chroma_store.py` `seed()` loads all 5 without error

**Todo List:**
- [ ] Write `data/seed_cyclones.json` — 5 real Bay-of-Bengal cyclones (e.g. Amphan 2020, Fani 2019, Phailin 2013, Hudhud 2014, Ockhi 2017)
- [ ] Implement `memory/chroma_store.py`: `ChromaStore` class with `seed(path)` and `retrieve(query, k=2)` using `all-MiniLM-L6-v2` embeddings

**Status:** [ ] pending

---

### ST-3 — LiteLLM Gateway + Cost Log
**Intent:** Single call surface for all LLM calls with automatic fallback (Granite 4 → Gemini → Groq) and per-call SQLite cost logging.

**Expected Outcomes:**
- `gateway/litellm_router.py` `complete(agent_name, model, messages)` returns LiteLLM response and writes one row to SQLite
- Fallback fires when primary model raises `litellm.exceptions.APIError`
- `gateway/cost_log.py` creates `costs.db` with schema `(id, ts, agent, model, tokens_in, tokens_out, usd_estimate)`

**Todo List:**
- [ ] Implement `cost_log.py`: `init_db()`, `log_call(agent, model, usage)` using `sqlite3`
- [ ] Implement `litellm_router.py`: `FALLBACK_ORDER = ["watsonx/ibm/granite-4-...", "gemini/gemini-pro", "groq/llama3-..."]`; wrap `litellm.completion()` with try/except fallback loop; call `log_call` after each successful response

**Relevant Context:** LiteLLM model strings for watsonx use prefix `watsonx/`; for Groq use `groq/`; for Gemini use `gemini/`.

**Status:** [ ] pending

---

### ST-4 — Three Agents + Supervisor
**Intent:** Implement the three specialised agents and a supervisor that runs them sequentially, passing context forward.

**Expected Outcomes:**
- `WeatherTrackAgent.run(cyclone_data: dict) → str` — weather/track summary using Granite 4
- `ImpactAgent.run(track_summary: str) → str` — impact assessment using Gemini
- `EvacuationAgent.run(impact_summary: str) → str` — evacuation plan using Groq
- `Supervisor.run(cyclone_data: dict) → dict` — runs all three in order, collects outputs, sets `pending_approval = True`

**Todo List:**
- [ ] Write `agents/base_agent.py`: `BaseAgent(name, model, system_prompt)` with `call_llm(messages) → str` delegating to `litellm_router.complete()`
- [ ] Write `agents/weather_track.py`: system prompt focused on track/intensity analysis
- [ ] Write `agents/impact.py`: system prompt focused on impact zone and population risk
- [ ] Write `agents/evacuation.py`: system prompt focused on shelter routing and evacuation order
- [ ] Write `agents/supervisor.py`: `Supervisor.run()` → sequential chain; appends RAG context from `ChromaStore.retrieve()` to each agent's user message; logs each step via `observability/logger.py`

**Status:** [ ] pending

---

### ST-5 — MCP Tool: QAOA Shelter Optimiser
**Intent:** Demonstrate MCP tool integration and quantum-classical comparison. The tool picks the optimal shelter given a list of candidates by solving a small QUBO with Qiskit QAOA on the Aer simulator, then validates against brute-force.

**Expected Outcomes:**
- `mcp/qaoa_shelter.py` exposes `optimise_shelters(shelters: list[dict]) → dict` returning `{best_shelter, method, objective_value}`
- QAOA runs on Qiskit Aer simulator (no real hardware needed)
- Brute-force fallback used when `len(shelters) > 8` or Qiskit unavailable
- `EvacuationAgent` calls this tool and includes result in its response

**Todo List:**
- [ ] Implement `mcp/qaoa_shelter.py`: encode shelter scores as QUBO; run QAOA with `p=1` on `AerSimulator`; brute-force fallback; return JSON
- [ ] Wire tool call into `EvacuationAgent.run()`: call `optimise_shelters()`, append result to prompt context

**Relevant Context:** Use `qiskit_algorithms.minimum_eigensolvers.QAOA` + `qiskit_aer.AerSimulator`. QUBO: maximise sum of capacity×score for selected shelters subject to count constraint.

**Status:** [ ] pending

---

### ST-6 — Regex Guardrail
**Intent:** Lightweight input/output validation without NeMo dependency overhead.

**Expected Outcomes:**
- `guardrails/regex_guard.py` blocks inputs containing prompt-injection patterns (`ignore previous`, `system:`, `<|im_start|>` etc.) and outputs containing PII patterns (Aadhaar-format numbers `\d{4}\s\d{4}\s\d{4}`)
- Raises `GuardError` with reason string on violation
- `Supervisor` calls `check_input()` before each agent and `check_output()` after

**Todo List:**
- [ ] Write `guardrails/regex_guard.py`: `INJECTION_PATTERNS` list + `PII_PATTERNS` list; `check_input(text)` and `check_output(text)` functions
- [ ] Add guard calls in `supervisor.py`

**Status:** [ ] pending

---

### ST-7 — Governance: policies.yaml + Audit Log
**Intent:** Declare per-agent policies and record every agent action in a tamper-evident audit log.

**Expected Outcomes:**
- `governance/policies.yaml` specifies `allowed_models`, `max_tokens`, `require_human_approval` per agent
- `governance/audit.py` writes one row per agent action to `audit.db` with SHA-256 hash of payload
- `Supervisor` loads policies at start; respects `require_human_approval` flag

**Todo List:**
- [ ] Write `governance/policies.yaml`
- [ ] Implement `governance/audit.py`: `init_db()`, `log_action(agent, action, payload)` — stores `sha256(json(payload))`
- [ ] Load policies in `supervisor.py`; pass `require_human_approval` flag to dashboard state

**Status:** [ ] pending

---

### ST-8 — Observability Logger
**Intent:** Structured JSON logging for every LLM call so the Gateway page can show timing and status.

**Expected Outcomes:**
- `observability/logger.py` uses `structlog` to emit JSON lines to stdout and `logs/app.log`
- `log_call(agent, model, duration_ms, status, tokens)` helper available

**Todo List:**
- [ ] Implement `observability/logger.py` with `structlog.configure()` and `log_call()` helper

**Status:** [ ] pending

---

### ST-9 — 3-Page Streamlit Dashboard
**Intent:** Minimal interactive UI covering Command Center (run pipeline), Alert Center (HITL approve), and Gateway (cost table).

**Expected Outcomes:**
- Page 1 **Command Center**: text input for cyclone params, "Run Pipeline" button, per-agent status badges (✅/⏳/❌), outputs displayed in expanders
- Page 2 **Alert Center**: last evacuation plan displayed, "✅ Approve & Dispatch" button writes approval to audit log, blocked until pipeline run
- Page 3 **Gateway**: reads `costs.db` via pandas, renders token/cost table + bar chart per agent/model

**Todo List:**
- [ ] Write `dashboard/app.py` with `st.sidebar.radio` navigation
- [ ] Page 1: call `Supervisor.run()` in a thread; stream status updates via `st.session_state`
- [ ] Page 2: show evacuation plan; approval button calls `audit.log_action(..., approved_by="operator")`
- [ ] Page 3: `pd.read_sql` from `costs.db`; `st.dataframe` + `st.bar_chart`

**Status:** [ ] pending

---

### ST-10 — Tests (3 pytest)
**Intent:** Verify the three core behaviours without requiring live API keys.

**Expected Outcomes:**
- `pytest tests/` passes with all 3 tests green using mocked LLM calls
- `test_agents.py` — patches `litellm.completion`, asserts each agent returns non-empty string
- `test_qaoa.py` — asserts QAOA `objective_value ≥` brute-force `objective_value` (or equal) for a 4-shelter fixture
- `test_rag.py` — seeds ChromaDB in a tmp dir; asserts `retrieve("cyclone storm surge")` returns ≥ 1 doc

**Todo List:**
- [ ] Write `tests/test_agents.py` using `unittest.mock.patch("litellm.completion")`
- [ ] Write `tests/test_qaoa.py` with deterministic 4-shelter fixture
- [ ] Write `tests/test_rag.py` using `tmp_path` fixture for ChromaDB dir

**Status:** [ ] pending

---

### ST-11 — README + Dockerfile
**Intent:** Step 16 deployment readiness. Any evaluator can `docker build` and run locally in one command.

**Expected Outcomes:**
- `README.md` covers: what it is, architecture summary, quickstart (venv + pip + streamlit run), Docker run, env var table
- `Dockerfile`: Python 3.12-slim, copies repo, pip installs, exposes 8501, CMD streamlit run

**Todo List:**
- [ ] Write `README.md`
- [ ] Write `Dockerfile`

**Status:** [ ] pending

---

## Master To-Do List

### Phase 1 — Planning & Architecture
- [x] Write `docs/plan.md` (this file)
- [ ] Write `data/seed_cyclones.json` (5 cyclone records)
- [ ] Write `.env.example` and `.gitignore`

### Phase 2 — Agent Development & Integration
- [ ] `agents/base_agent.py` + `gateway/litellm_router.py` + `gateway/cost_log.py`
- [ ] `agents/weather_track.py`, `agents/impact.py`, `agents/evacuation.py`
- [ ] `agents/supervisor.py` (orchestration + RAG context injection)
- [ ] `mcp/qaoa_shelter.py` (QAOA on Aer sim + brute-force fallback)
- [ ] Wire QAOA tool into `EvacuationAgent`

### Phase 3 — Intelligence & Monitoring
- [ ] `memory/chroma_store.py` (seed + retrieve, 5 notes)
- [ ] `observability/logger.py` (structlog JSON)

### Phase 4 — Security & Application Development
- [ ] `guardrails/regex_guard.py` + guard calls in supervisor
- [ ] `governance/policies.yaml` + `governance/audit.py`
- [ ] `dashboard/app.py` — 3 pages

### Phase 5 — Testing & Deployment
- [ ] `tests/test_agents.py`, `tests/test_qaoa.py`, `tests/test_rag.py`
- [ ] `README.md` + `Dockerfile`
