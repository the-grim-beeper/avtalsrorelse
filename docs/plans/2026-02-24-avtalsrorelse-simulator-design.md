# Avtalsrörelsen Simulator — Design Document

## Overview

A round-based multiagent simulation where 13 LLM-powered actors negotiate collective agreements in a Swedish avtalsrörelse. Users configure macroeconomic parameters via scenario presets and watch negotiations unfold in a war room interface.

**Purpose:** Analytical sandbox — knowledgeable users tweak parameters and observe how negotiations play out differently.

**Stack:** FastAPI + React/Vite/TS + Anthropic Claude API, deployed on Railway.

## Architecture

```
┌─────────────────────────────────────┐
│         React/Vite Frontend         │
│  ┌───────────┐  ┌────────────────┐  │
│  │ Setup View │  │  War Room View │  │
│  └───────────┘  └────────────────┘  │
│            SSE streaming ↑          │
├─────────────────────────────────────┤
│         FastAPI Backend             │
│  ┌──────────────────────────────┐   │
│  │    Simulation Engine         │   │
│  │  Round Runner, Agent Manager │   │
│  │  Scenario Engine, Mediator   │   │
│  └──────────────────────────────┘   │
│         Anthropic Claude API ↓      │
└─────────────────────────────────────┘
```

- Frontend streams simulation via SSE
- Backend orchestrates rounds, makes parallel LLM calls
- No database — state in memory, clean Pydantic models for future persistence
- Railway: two services (backend + frontend), ANTHROPIC_API_KEY as env var

## Agents (13 total, 4 tiers)

### Tier 1: Norm-setting (Industriavtalet) — negotiates first, sets märket
- **IF Metall** — Blue-collar industrial union. Real wage growth, working conditions, LO solidarity.
- **Unionen** — White-collar industrial union. Salary development, competence, flexibility.
- **Teknikföretagen** — Engineering employers. Export competitiveness, labor cost predictability.

### Tier 2: Private sector — follows after märket
- **Handels** — Retail union. Low-wage uplift, scheduling, part-time rights.
- **Svensk Handel** — Retail employers. Margins, flexible staffing, cost control.
- **Almega** — Service sector employers. Differentiated wages, individual salary setting.

### Tier 3: Public sector — negotiates last, tax-revenue constrained
- **Kommunal** — Municipal blue-collar. Wage gap to private sector, staffing.
- **Vision** — Municipal white-collar. Professional development, wage structure.
- **Vårdförbundet** — Healthcare professionals. Special demands, working hours.
- **SKR** — Municipalities & regions employer. Budget constraints, recruitment.

### Tier 4: Confederations & mediator
- **LO** — Blue-collar confederation. Solidarity coordination, low-wage profiles.
- **Svenskt Näringsliv** — Employer confederation. Overall cost norm, competitiveness.
- **Medlingsinstitutet** — National Mediation Office. Settlement, märket compliance, industrial peace.

### Agent data model
Each agent has:
- `identity`: Name, role description, institutional mandate
- `priorities`: Ranked interests derived from scenario
- `constraints`: Hard limits (e.g. SKR budget ceiling)
- `relationships`: Stance toward other agents
- `state`: Current demand/offer, satisfaction, willingness to settle (0-100)

### Agent prompt structure
```
You are {name}, {role_description}.

MACRO ENVIRONMENT: {scenario parameters}
YOUR MANDATE: {priorities and constraints}
CURRENT NEGOTIATION STATE: {round, positions, history}

Decide your action. Respond with: position, reasoning, public statement, willingness to settle (0-100).
```

Sonnet for reasoning, Haiku for summaries.

## Simulation Mechanics

### 5 phases, ~10-16 rounds total

**Phase 1: Opening Positions (1 round)**
All 13 agents declare opening demands/mandates. LO and Svenskt Näringsliv set coordination signals.

**Phase 2: Industriavtalet (3-6 rounds)**
Tier 1 negotiates. Others observe and comment. Medlingsinstitutet monitors.
- Gap narrows below threshold → settlement (märket set)
- Stalled after 4 rounds → Medlingsinstitutet intervenes
- Max 6 rounds, forced mediation if needed

**Phase 3: Private Sector (2-4 rounds)**
Tier 2 negotiates within the märket norm. Can argue for deviations but face institutional pressure.

**Phase 4: Public Sector (2-4 rounds)**
Tier 3 negotiates. SKR budget constraint vs union demands for märket-level increases. Strike threats most likely here.

**Phase 5: Summary (1 round)**
Haiku generates briefing: all agreements, comparison to märket, key tensions, winners/losers.

### Settlement mechanics
- Willingness to settle (0-100) per agent
- Both sides > 70 → agreement reached
- Medlingsinstitutet proposals boost willingness
- Willingness < 40 for 3+ rounds → strike/lockout threat
- Strike threats shift dynamics: employer willingness up, but counter-demands rise
- Medlingsinstitutet can call cooling-off period

## Scenario Presets & Parameters

### Macro parameters
| Parameter | Range | Default |
|-----------|-------|---------|
| Inflation (KPI) | 0-15% | 2.0% |
| Unemployment | 2-15% | 7.0% |
| GDP growth | -5 to +8% | 2.0% |
| Riksbank policy rate | -0.5 to 10% | 2.5% |
| Political climate | Left ←→ Right (1-5) | 3 |
| Export pressure | Low/Medium/High | Medium |
| Previous agreement (märket) | 0-8% | 2.5% |

### Presets
| Preset | Description |
|--------|-------------|
| **Stabil tillväxt (2017)** | Low inflation, moderate growth. Calm round. |
| **Inflationschock (2023)** | 10%+ inflation, rising rates, cost-of-living crisis. |
| **90-talskrisen** | Deep recession, high unemployment, fiscal crisis. |
| **Högkonjunktur** | Boom, labor shortage, strong profits. |
| **Grön omställning** | Structural transition, competence demands. |
| **Pandemiåterhämtning** | Uneven recovery, strained public finances. |

## Frontend UI

### Setup View
- Scenario presets as selectable cards
- Parameter sliders auto-populate from preset, remain editable
- Agent roster overview
- "Starta förhandling" launch button

### War Room View (three columns)
- **Left:** Agent roster cards — name, position, sentiment color (green/yellow/red), willingness bar. Click to expand reasoning.
- **Center:** Round header, phase progress, active negotiation pairs with gap indicators, streaming action feed, public statements as quotes. Strike events get dramatic treatment.
- **Right:** Macro summary, round timeline, settlement tracker checklist, final outcome summary.

### Visual style — Scandinavian clean
- White/light gray background, generous whitespace
- Swedish blue (#006AA7) primary, gold (#FECC02) highlights
- Clean sans-serif (Inter), clear hierarchy
- Subtle animations: cards slide in, numbers transition, sentiment colors shift
- Information density managed through expand/collapse

## Technical Details

### Backend structure
```
backend/app/
  main.py, config.py
  models/     — agents.py, scenario.py, simulation.py
  agents/     — base.py, definitions.py, prompts.py
  engine/     — runner.py, mediator.py, settlement.py
  scenarios/  — presets.py
  api/        — routes.py
  services/   — llm.py
```

### Frontend structure
```
frontend/src/
  App.tsx
  pages/      — SetupPage.tsx, SimulationPage.tsx
  components/
    setup/    — PresetCard, ParameterSliders, AgentRoster
    warroom/  — AgentPanel, AgentCard, CenterStage, RoundHeader,
                NegotiationPair, ActionFeed, InfoPanel,
                RoundTimeline, SettlementTracker, MacroSummary
  api/        — client.ts
  types/      — index.ts
  hooks/      — useSimulation.ts
```

### SSE events
```
round_start, agent_action, settlement, conflict_event,
mediation, round_end, simulation_end
```

### LLM strategy
- Parallel calls within each round (asyncio.gather)
- Sonnet for reasoning (~500 tokens/agent/round)
- Haiku for summaries and public statement formatting
- Structured JSON output
- Estimated cost: ~$0.30-0.80 per simulation

### Railway deployment
- Two services: backend (Python 3.12, Uvicorn) + frontend (Node 20, Vite build)
- Env: ANTHROPIC_API_KEY
- No database, no volumes
