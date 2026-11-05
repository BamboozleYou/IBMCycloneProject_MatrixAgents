# Reference Summary

## (a) Cyclone Problem Statement — Suggested Agents & Data

**Source:** `reference/extracted/sugesstions.docx.txt`

**Challenge:** *Cyclone Detection & Early Warning System* — Domain: Disaster Management & Climate Resilience.

Coastal regions along India's Bay of Bengal and Arabian Sea are vulnerable to cyclones, storm surges, and severe weather. Delayed detection and limited early-warning access put lives, infrastructure, and agriculture at risk. The objective is an **Agentic AI-based system** that analyses meteorological and satellite data, detects cyclone formations, predicts trajectories and intensity, assesses impact zones, and generates actionable alerts.

### Suggested AI Agents (7)

| # | Agent | Responsibility |
|---|---|---|
| 1 | Weather Data Analysis Agent | Atmospheric pressure, wind speed, humidity, rainfall, sea surface temperature |
| 2 | Cyclone Detection Agent | Satellite imagery + weather pattern analysis for formation identification |
| 3 | Cyclone Tracking & Prediction Agent | Movement, direction, speed, landfall prediction |
| 4 | Cyclone Intensity Prediction Agent | Intensity estimation, rapid-intensification detection |
| 5 | Impact Assessment Agent | Vulnerable regions, risks to population/infrastructure/agriculture |
| 6 | Early Warning & Alert Agent | Location-specific alerts and preparedness recommendations |
| 7 | Disaster Response Recommendation Agent | Evacuation prep, resource allocation, shelter identification |

### Suggested Data Sources

- Historical cyclone datasets and track records
- Satellite imagery and cloud movement data
- Sea surface temperature, atmospheric pressure, humidity
- Wind speed/direction, rainfall/precipitation
- Coastal geographical and elevation data
- Population density and vulnerable settlement info
- Historical cyclone impact/damage records
- Weather forecast and meteorological observations
- **Providers:** IMD, NOAA, NASA, public met datasets

### Technology Stack

IBM Bob + IBM Granite LLM + IBM Cloud, Python 3.12, Streamlit / Render / Vercel / IBM Cloud deployment, OmniRoute LLM gateway, NeMo Guardrails, vector database (RAG), agent architecture: sequential / hierarchical / hybrid.

### LLM Assignment (from mentor notes)

| Agent slot | LLM |
|---|---|
| Agent 1 | IBM Granite 4 (via watsonx.ai) |
| Agent 2 | Google Gemini |
| Agent 3 | Groq-supported LLM |

---

## (b) Sample PPT Slide Structure

**Source:** `reference/extracted/Sample_PPT Template_Bengaluru_Hackathon_2026.pptx.txt` (6 slides)

| Slide | Title / Purpose | Key Content |
|---|---|---|
| 1 | **Title slide** | "Edunet Hackathon in collaboration with IBM SkillsBuild on IBM Bob" |
| 2 | **Project overview** (combined slide) | Team info, project name, problem need, methodology, IBM tools used, conclusion & demo impact |
| 3 | **Development with IBM Bob** | 9-step Bob workflow: Requirements → Bob Creates Plan → Review & Refine → Code Generation → Review Output → Run & Validate → Bob Explains → Quality & Tests → Documentation |
| 4 | **IBM Bob — Files & Code Generated** | Two-panel: Bob-generated project file structure screenshot + Bob code generation session screenshot |
| 5 | **Features of the Project** | Multi-agent AI system, domain-specific features, differentiators |
| 6 | **Novelty & Future Scope** | Left: novelty/uniqueness points; Right: future scope items |

> **Note:** The sample PPT uses a water-management domain ("Salinity Shield AI / GreenPulse AI"). Slides 3–6 define the **structural template** all teams must follow; content is replaced with the team's own project.

---

## (c) Sample Video Structure & Timing

**Source:** `reference/extracted/Sample_Video_Template_Bengaluru_Hackathon_2026.mp4` — total ~**210 seconds (3 min 30 s)**, 22 frames at 10 s intervals.

| Timestamp | Content visible |
|---|---|
| 0 s | **Title slide** — hackathon branding |
| 10–20 s | Title / opening section |
| 30–50 s | **Slide 2 — Project overview** — team names, project description, methodology, IBM tools, conclusion |
| 60–70 s | **Slide 4 — IBM Bob Files & Code Generated** — Bob file explorer + code generation screenshots |
| 80–100 s | **Live application demo begins** — dashboard home, dark-themed UI, left nav with multiple sections |
| 110–150 s | **Dashboard deep-dive** — Predictive Maintenance / Risk Matrix / Priority Queue pages |
| 160–200 s | **Alert Center page** — live alerts, AI Explanation panel, HITL "Mark Resolved" action |
| 210 s | **Slide 6 — Novelty & Future Scope** — closing slide |

### Structural pattern for our own video

1. Title slide (~10 s)
2. Project overview / team slide (~20 s)
3. IBM Bob development workflow slide (~15 s)
4. Bob-generated code/files screenshot slide (~10 s)
5. Features slide (~15 s)
6. Live dashboard walkthrough — the bulk (~2 min, navigate several pages)
7. Novelty & Future Scope slide (~10 s)

---

## (d) The Mentor's 16 Steps

**Source:** `mentor_framework.md`

Grouped into 5 phases:

### Phase 1 — Planning & Architecture

1. **Problem Identification & Requirement Analysis** → deliverable: project scope & requirement doc
2. **System Architecture & Technology Stack** → deliverable: architecture diagram & tech stack
3. **Development Environment Setup Using IBM Bob** → deliverable: configured environment & project structure (use Ask / Plan / Agent modes)
4. **Data Source Identification & Integration** → deliverable: working data integration pipeline

### Phase 2 — Agent Development & Integration

5. **Specialized AI Agent Development** → min. 3 agents with defined roles, tools, LLMs → deliverable: 3+ functional agents
6. **Multi-Agent Orchestration & Collaboration** → Master Orchestrator, sequential + parallel execution → deliverable: working MAS with centralised orchestration
7. **Multiple LLM Provider Integration** → IBM Granite (watsonx.ai) + Gemini + Groq, fallback routing, cost/latency eval → deliverable: multi-LLM app
8. **MCP-Based Tool Integration** → MCP servers, external APIs/DBs, tool auth → deliverable: MCP-enabled agents

### Phase 3 — Intelligence & Monitoring

9. **Agent Memory & Vector Database Integration** → short + long-term memory, embeddings, RAG → deliverable: memory-enabled app with vector DB
10. **LLM Gateway & Token-Cost Monitoring** → centralised gateway, per-agent token tracking, budget limits → deliverable: gateway + cost dashboard
11. **Observability & Agent Performance Evaluation** → logging, tracing, LLM/MCP monitoring, performance reports → deliverable: observability framework

### Phase 4 — Security & Application Development

12. **Guardrails, Security & Human-in-the-Loop** → input/output validation, prompt injection protection, RBAC, human approval → deliverable: secure app with human oversight
13. **AI Governance & Agent Control Policies** → agent boundaries, decision policies, audit logging → deliverable: governance framework
14. **Dashboard & Application Development** → interactive UI, agent status, token-cost analytics, HITL interface → deliverable: fully functional app with dashboard

### Phase 5 — Testing & Deployment

15. **Testing & Performance Evaluation** → unit, integration, security, RAG, guardrail testing → deliverable: tested & validated solution
16. **Application Deployment & Production Readiness** → Docker, IBM Cloud, env/secrets, health checks, monitoring → deliverable: deployed & operational app

### Evaluation Criteria (max 20 pts)

| Criterion | Points |
|---|---|
| Completeness & Feasibility | 5 |
| Creativity & Innovation | 5 |
| Design & Usability | 5 |
| Effectiveness & Efficiency | 5 |

### Minimum Expected Deliverables

Working app · interactive dashboard · ≥3 agents · multiple LLMs · MCP tools · vector DB + RAG · LLM gateway with cost monitoring · observability · guardrails + HITL · AI governance · IBM Cloud deployment.
