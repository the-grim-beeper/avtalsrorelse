# Avtalsrörelsen Simulator — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a multiagent LLM simulation of Swedish collective bargaining with 13 agents, configurable scenarios, and a real-time war room UI.

**Architecture:** FastAPI backend orchestrates round-based negotiation between 13 LLM-powered agents via Anthropic Claude API. React/Vite frontend connects via SSE to stream round results into a three-column war room view. No database — all state in memory.

**Tech Stack:** Python 3.12, FastAPI, Anthropic SDK, Pydantic; React 18, TypeScript, Vite, TailwindCSS v4; Railway for deployment.

**Design doc:** `docs/plans/2026-02-24-avtalsrorelse-simulator-design.md`

---

## Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/{models,agents,engine,scenarios,api,services}
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/agents/__init__.py
touch backend/app/engine/__init__.py
touch backend/app/scenarios/__init__.py
touch backend/app/api/__init__.py
touch backend/app/services/__init__.py
```

**Step 2: Write requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
anthropic==0.43.0
pydantic==2.10.4
pydantic-settings==2.7.1
sse-starlette==2.2.1
python-dotenv==1.0.1
```

**Step 3: Write config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    sonnet_model: str = "claude-sonnet-4-5-20250514"
    haiku_model: str = "claude-haiku-4-5-20251001"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}


settings = Settings()
```

**Step 4: Write main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Avtalsrörelsen Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 5: Create .env for local dev**

```
ANTHROPIC_API_KEY=your-key-here
```

Add `.env` to `.gitignore`.

**Step 6: Install dependencies and verify**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# GET http://localhost:8000/health → {"status": "ok"}
```

**Step 7: Commit**

```bash
git add backend/ .gitignore
git commit -m "feat: scaffold backend with FastAPI, config, and health endpoint"
```

---

## Task 2: Pydantic Data Models

**Files:**
- Create: `backend/app/models/scenario.py`
- Create: `backend/app/models/agents.py`
- Create: `backend/app/models/simulation.py`

**Step 1: Write scenario models**

```python
# backend/app/models/scenario.py
from enum import Enum
from pydantic import BaseModel, Field


class ExportPressure(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MacroParameters(BaseModel):
    inflation: float = Field(2.0, ge=0, le=15, description="KPI inflation %")
    unemployment: float = Field(7.0, ge=2, le=15, description="Unemployment %")
    gdp_growth: float = Field(2.0, ge=-5, le=8, description="GDP growth %")
    policy_rate: float = Field(2.5, ge=-0.5, le=10, description="Riksbank policy rate %")
    political_climate: int = Field(3, ge=1, le=5, description="1=Left, 5=Right")
    export_pressure: ExportPressure = ExportPressure.MEDIUM
    previous_agreement: float = Field(2.5, ge=0, le=8, description="Previous märket %")


class ScenarioPreset(BaseModel):
    id: str
    name: str
    description: str
    flavor_text: str
    parameters: MacroParameters
```

**Step 2: Write agent models**

```python
# backend/app/models/agents.py
from enum import Enum
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    UNION = "union"
    EMPLOYER = "employer"
    CONFEDERATION = "confederation"
    MEDIATOR = "mediator"


class AgentTier(int, Enum):
    NORM_SETTING = 1
    PRIVATE_SECTOR = 2
    PUBLIC_SECTOR = 3
    META = 4


class Relationship(str, Enum):
    ALLIED = "allied"
    OPPOSED = "opposed"
    NEUTRAL = "neutral"


class AgentIdentity(BaseModel):
    id: str
    name: str
    short_name: str
    agent_type: AgentType
    tier: AgentTier
    role_description: str
    priorities: list[str]
    constraints: list[str]
    relationships: dict[str, Relationship] = {}


class AgentState(BaseModel):
    agent_id: str
    current_position: float | None = None  # wage demand/offer %
    willingness_to_settle: int = Field(50, ge=0, le=100)
    rounds_at_low_willingness: int = 0
    has_threatened_action: bool = False
    is_settled: bool = False
    settlement_level: float | None = None


class AgentAction(BaseModel):
    agent_id: str
    round_number: int
    phase: int
    position: float  # wage demand/offer %
    reasoning: str  # internal reasoning (visible to user)
    public_statement: str
    willingness_to_settle: int = Field(ge=0, le=100)
```

**Step 3: Write simulation models**

```python
# backend/app/models/simulation.py
from enum import Enum
from pydantic import BaseModel, Field

from app.models.agents import AgentAction, AgentState
from app.models.scenario import MacroParameters


class Phase(int, Enum):
    OPENING = 1
    INDUSTRIAVTALET = 2
    PRIVATE_SECTOR = 3
    PUBLIC_SECTOR = 4
    SUMMARY = 5


class NegotiationPair(BaseModel):
    union_ids: list[str]
    employer_id: str
    phase: Phase
    is_settled: bool = False
    settlement_level: float | None = None
    settlement_round: int | None = None


class ConflictEvent(BaseModel):
    event_type: str  # "strike_threat", "lockout_threat", "cooling_off"
    agent_id: str
    round_number: int
    description: str


class RoundResult(BaseModel):
    round_number: int
    phase: Phase
    actions: list[AgentAction]
    settlements: list[NegotiationPair] = []
    conflict_events: list[ConflictEvent] = []
    summary: str = ""


class SimulationState(BaseModel):
    id: str
    parameters: MacroParameters
    preset_id: str | None = None
    current_round: int = 0
    current_phase: Phase = Phase.OPENING
    agent_states: dict[str, AgentState] = {}
    rounds: list[RoundResult] = []
    negotiation_pairs: list[NegotiationPair] = []
    marke: float | None = None  # set when industriavtalet settles
    is_complete: bool = False
    final_summary: str = ""
```

**Step 4: Verify imports work**

```bash
cd backend && python -c "from app.models.simulation import SimulationState; print('OK')"
```

**Step 5: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add Pydantic data models for agents, scenarios, and simulation"
```

---

## Task 3: Agent Definitions

**Files:**
- Create: `backend/app/agents/definitions.py`

**Step 1: Write all 13 agent definitions**

```python
# backend/app/agents/definitions.py
from app.models.agents import AgentIdentity, AgentType, AgentTier, Relationship

AGENTS: dict[str, AgentIdentity] = {
    "if_metall": AgentIdentity(
        id="if_metall",
        name="IF Metall",
        short_name="IF Metall",
        agent_type=AgentType.UNION,
        tier=AgentTier.NORM_SETTING,
        role_description=(
            "Sweden's largest industrial union representing 300,000 blue-collar "
            "workers in manufacturing, mining, and engineering. You are a key party "
            "to Industriavtalet and your settlement sets the 'märket' — the norm "
            "for all other agreements. You balance aggressive wage demands with "
            "responsibility for the export sector's competitiveness."
        ),
        priorities=[
            "Real wage growth that at minimum compensates for inflation",
            "Solidarity wage policy — lift the lowest-paid workers",
            "Working conditions and safety improvements",
            "Coordinated approach with LO affiliates",
        ],
        constraints=[
            "Must not undermine Swedish export competitiveness",
            "Bound by Industriavtalet framework — must negotiate in good faith",
            "Must consider LO coordination signals",
        ],
        relationships={
            "teknikforetagen": Relationship.OPPOSED,
            "unionen": Relationship.ALLIED,
            "lo": Relationship.ALLIED,
        },
    ),
    "unionen": AgentIdentity(
        id="unionen",
        name="Unionen",
        short_name="Unionen",
        agent_type=AgentType.UNION,
        tier=AgentTier.NORM_SETTING,
        role_description=(
            "Sweden's largest white-collar union with 700,000 members in the "
            "private sector, particularly in engineering and tech. You are a party "
            "to Industriavtalet. You focus on individual salary development and "
            "competence-building alongside the collective agreement."
        ),
        priorities=[
            "Salary development that rewards competence and performance",
            "Investment in education and reskilling",
            "Work-life balance and flexible working arrangements",
            "A märket level that reflects productivity gains",
        ],
        constraints=[
            "Bound by Industriavtalet — coordinate with IF Metall",
            "Must balance collective norms with individual salary setting",
        ],
        relationships={
            "teknikforetagen": Relationship.OPPOSED,
            "if_metall": Relationship.ALLIED,
        },
    ),
    "teknikforetagen": AgentIdentity(
        id="teknikforetagen",
        name="Teknikföretagen",
        short_name="Teknikftg",
        agent_type=AgentType.EMPLOYER,
        tier=AgentTier.NORM_SETTING,
        role_description=(
            "The employer organization for Sweden's engineering and tech industry, "
            "representing 4,100 companies. You negotiate Industriavtalet against "
            "IF Metall and Unionen. Your settlement becomes the märket. You must "
            "protect Swedish export industry competitiveness above all."
        ),
        priorities=[
            "Keep labor cost increases below productivity growth",
            "Predictable cost development for long-term planning",
            "Flexibility in local wage formation",
            "Maintain international competitiveness",
        ],
        constraints=[
            "Must agree to Industriavtalet framework",
            "Cannot ignore Svenskt Näringsliv coordination signals",
            "Must balance member companies' varying ability to pay",
        ],
        relationships={
            "if_metall": Relationship.OPPOSED,
            "unionen": Relationship.OPPOSED,
            "svenskt_naringsliv": Relationship.ALLIED,
        },
    ),
    "handels": AgentIdentity(
        id="handels",
        name="Handelsanställdas förbund",
        short_name="Handels",
        agent_type=AgentType.UNION,
        tier=AgentTier.PRIVATE_SECTOR,
        role_description=(
            "The union for 150,000 workers in retail, warehousing, and e-commerce. "
            "Your members are among the lowest-paid in Sweden. You fight hard for "
            "low-wage uplifts and better working conditions in a sector with many "
            "part-time and precarious workers."
        ),
        priorities=[
            "Wage increases above the märket for the lowest-paid",
            "Minimum wage floor increases",
            "Better scheduling predictability",
            "Full-time employment as the norm",
        ],
        constraints=[
            "Strong institutional pressure to stay close to märket",
            "Must coordinate with LO",
            "Retail sector margins limit employer flexibility",
        ],
        relationships={
            "svensk_handel": Relationship.OPPOSED,
            "lo": Relationship.ALLIED,
            "if_metall": Relationship.ALLIED,
        },
    ),
    "svensk_handel": AgentIdentity(
        id="svensk_handel",
        name="Svensk Handel",
        short_name="Sv Handel",
        agent_type=AgentType.EMPLOYER,
        tier=AgentTier.PRIVATE_SECTOR,
        role_description=(
            "The employer organization for Sweden's retail and wholesale sector, "
            "representing 9,000 companies. You operate in a low-margin, highly "
            "competitive sector. Labor is your biggest cost. You must keep wage "
            "increases manageable while maintaining your workforce."
        ),
        priorities=[
            "Total cost increases at or below the märket",
            "Flexibility in staffing and scheduling",
            "Resist above-märket low-wage uplifts",
            "Individual performance-based pay",
        ],
        constraints=[
            "Thin margins — cannot absorb large cost increases",
            "Must stay close to the märket norm",
            "Coordinate with Svenskt Näringsliv",
        ],
        relationships={
            "handels": Relationship.OPPOSED,
            "svenskt_naringsliv": Relationship.ALLIED,
        },
    ),
    "almega": AgentIdentity(
        id="almega",
        name="Almega",
        short_name="Almega",
        agent_type=AgentType.EMPLOYER,
        tier=AgentTier.PRIVATE_SECTOR,
        role_description=(
            "The employer organization for Sweden's service sector — IT, consulting, "
            "staffing, media, and more. You represent a diverse, knowledge-intensive "
            "sector where individual salary setting is the norm. You push for "
            "differentiated agreements that reflect your sector's unique dynamics."
        ),
        priorities=[
            "Sifferlösa avtal — agreements without fixed percentage increases",
            "Individual and differentiated salary setting",
            "Flexibility and mobility in the labor market",
            "Keep total cost at or below märket",
        ],
        constraints=[
            "Must align with Svenskt Näringsliv overall strategy",
            "Pressure from the märket norm even in knowledge sectors",
        ],
        relationships={
            "svenskt_naringsliv": Relationship.ALLIED,
            "unionen": Relationship.OPPOSED,
        },
    ),
    "kommunal": AgentIdentity(
        id="kommunal",
        name="Kommunal",
        short_name="Kommunal",
        agent_type=AgentType.UNION,
        tier=AgentTier.PUBLIC_SECTOR,
        role_description=(
            "Sweden's largest union with 500,000 members — nursing assistants, "
            "childcare workers, home care providers, and other municipal blue-collar "
            "workers. Your members are predominantly women in physically and "
            "emotionally demanding jobs. You fight to close the wage gap between "
            "the public and private sectors."
        ),
        priorities=[
            "Close the wage gap to private sector equivalents",
            "Above-märket increases for the lowest-paid",
            "Better staffing ratios and working conditions",
            "Recognition of the value of care work",
        ],
        constraints=[
            "SKR budget is limited by tax revenue",
            "Institutional pressure to respect the märket",
            "LO solidarity may both help and constrain",
        ],
        relationships={
            "skr": Relationship.OPPOSED,
            "lo": Relationship.ALLIED,
            "vardforbundet": Relationship.ALLIED,
        },
    ),
    "vision": AgentIdentity(
        id="vision",
        name="Vision",
        short_name="Vision",
        agent_type=AgentType.UNION,
        tier=AgentTier.PUBLIC_SECTOR,
        role_description=(
            "A white-collar union representing 200,000 members in municipalities, "
            "regions, churches, and private companies in the welfare sector. You "
            "focus on professional development, career paths, and attractive "
            "working conditions in the public sector."
        ),
        priorities=[
            "Competitive salaries to attract and retain talent",
            "Career development and professional growth",
            "Wage structure reform in the public sector",
            "Keep pace with private sector white-collar wages",
        ],
        constraints=[
            "Bound by SKR's budget reality",
            "Must coordinate with other public sector unions",
        ],
        relationships={
            "skr": Relationship.OPPOSED,
            "kommunal": Relationship.ALLIED,
        },
    ),
    "vardforbundet": AgentIdentity(
        id="vardforbundet",
        name="Vårdförbundet",
        short_name="Vårdfb",
        agent_type=AgentType.UNION,
        tier=AgentTier.PUBLIC_SECTOR,
        role_description=(
            "The union for 115,000 nurses, midwives, biomedical scientists, and "
            "radiographers. You represent highly educated professionals whose "
            "wages have historically lagged behind comparable private-sector "
            "professions. You are the most likely public sector union to threaten "
            "industrial action."
        ),
        priorities=[
            "Significant above-märket increases to fix structural underpayment",
            "Reduced working hours and better work-life balance",
            "Recognition of specialist competence in pay",
            "Safe staffing levels",
        ],
        constraints=[
            "Healthcare is essential — strikes have immediate public impact",
            "SKR budget constraints are real",
            "Must maintain public sympathy",
        ],
        relationships={
            "skr": Relationship.OPPOSED,
            "kommunal": Relationship.ALLIED,
        },
    ),
    "skr": AgentIdentity(
        id="skr",
        name="Sveriges Kommuner och Regioner",
        short_name="SKR",
        agent_type=AgentType.EMPLOYER,
        tier=AgentTier.PUBLIC_SECTOR,
        role_description=(
            "The employer organization for Sweden's 290 municipalities and 21 "
            "regions. You employ over 1 million people — the country's largest "
            "employer category. Your budget depends on tax revenue and government "
            "grants. You must balance recruitment needs against fiscal reality."
        ),
        priorities=[
            "Keep total cost increases within budget (tax revenue growth)",
            "Recruitment and retention of key staff",
            "Flexibility in local salary setting",
            "Manageable total cost — cannot exceed fiscal space",
        ],
        constraints=[
            "Budget ceiling set by tax revenue growth and government grants",
            "Cannot print money — must balance books",
            "Political climate affects government grant levels",
            "Public sector agreements must broadly follow the märket",
        ],
        relationships={
            "kommunal": Relationship.OPPOSED,
            "vision": Relationship.OPPOSED,
            "vardforbundet": Relationship.OPPOSED,
            "svenskt_naringsliv": Relationship.NEUTRAL,
        },
    ),
    "lo": AgentIdentity(
        id="lo",
        name="Landsorganisationen",
        short_name="LO",
        agent_type=AgentType.CONFEDERATION,
        tier=AgentTier.META,
        role_description=(
            "The Swedish Trade Union Confederation representing 14 blue-collar "
            "unions with 1.5 million members. You coordinate solidarity wage "
            "policy across affiliates. You don't negotiate directly but you set "
            "coordination signals and strategy that your affiliates are expected "
            "to follow. Your influence is political and strategic."
        ),
        priorities=[
            "Solidarity wage policy — compress wage differences",
            "Extra increases for the lowest-paid workers",
            "Coordinate a unified union front",
            "Defend the Swedish model and collective bargaining",
        ],
        constraints=[
            "Cannot force affiliates — coordination is voluntary",
            "Must balance different affiliates' needs",
            "Must respect Industriavtalet's norm-setting role",
        ],
        relationships={
            "if_metall": Relationship.ALLIED,
            "handels": Relationship.ALLIED,
            "kommunal": Relationship.ALLIED,
            "svenskt_naringsliv": Relationship.OPPOSED,
        },
    ),
    "svenskt_naringsliv": AgentIdentity(
        id="svenskt_naringsliv",
        name="Svenskt Näringsliv",
        short_name="Sv Närliv",
        agent_type=AgentType.CONFEDERATION,
        tier=AgentTier.META,
        role_description=(
            "The Confederation of Swedish Enterprise representing 60,000 member "
            "companies. You set the overall employer strategy for the avtalsrörelse. "
            "Your top priority is keeping total labor cost increases in line with "
            "productivity growth and international competitiveness. You coordinate "
            "employer organizations to hold the line."
        ),
        priorities=[
            "Total cost norm at or below productivity growth",
            "Defend the märket as a ceiling, not a floor",
            "Employer flexibility and individual salary setting",
            "International competitiveness of Swedish business",
        ],
        constraints=[
            "Cannot force member organizations — coordination role",
            "Must maintain credibility with both members and public",
        ],
        relationships={
            "teknikforetagen": Relationship.ALLIED,
            "svensk_handel": Relationship.ALLIED,
            "almega": Relationship.ALLIED,
            "lo": Relationship.OPPOSED,
        },
    ),
    "medlingsinstitutet": AgentIdentity(
        id="medlingsinstitutet",
        name="Medlingsinstitutet",
        short_name="MI",
        agent_type=AgentType.MEDIATOR,
        tier=AgentTier.META,
        role_description=(
            "The Swedish National Mediation Office — a government agency tasked "
            "with mediating labor disputes and promoting wage formation in line "
            "with economic conditions. You are neutral but your mandate is to "
            "ensure industrial peace and that the märket functions as the norm. "
            "You intervene when negotiations stall."
        ),
        priorities=[
            "Achieve settlements without industrial action",
            "Ensure the märket is respected across sectors",
            "Promote wage formation consistent with economic balance",
            "Maintain trust from both sides",
        ],
        constraints=[
            "Must remain neutral — cannot side with unions or employers",
            "Can propose compromises but cannot force agreements",
            "Can postpone industrial action for up to 14 days",
        ],
        relationships={},  # neutral to all
    ),
}
```

**Step 2: Verify**

```bash
cd backend && python -c "from app.agents.definitions import AGENTS; print(f'{len(AGENTS)} agents loaded')"
# Expected: 13 agents loaded
```

**Step 3: Commit**

```bash
git add backend/app/agents/definitions.py
git commit -m "feat: define all 13 agent identities with roles, priorities, and constraints"
```

---

## Task 4: Scenario Presets

**Files:**
- Create: `backend/app/scenarios/presets.py`

**Step 1: Write all 6 presets**

```python
# backend/app/scenarios/presets.py
from app.models.scenario import ExportPressure, MacroParameters, ScenarioPreset

PRESETS: dict[str, ScenarioPreset] = {
    "stabil_tillvaxt": ScenarioPreset(
        id="stabil_tillvaxt",
        name="Stabil tillväxt (2017)",
        description="Low inflation, moderate growth, low interest rates. A calm and predictable negotiation round.",
        flavor_text=(
            "The Swedish economy is humming along nicely. Inflation is below target, "
            "growth is steady, and the labor market is balanced. The Riksbank is still "
            "in negative rate territory. There is no crisis, no urgency — just the "
            "routine machinery of the Swedish model. Both sides expect a modest, "
            "uncontroversial settlement."
        ),
        parameters=MacroParameters(
            inflation=1.8,
            unemployment=6.7,
            gdp_growth=2.4,
            policy_rate=-0.5,
            political_climate=3,
            export_pressure=ExportPressure.MEDIUM,
            previous_agreement=2.2,
        ),
    ),
    "inflationschock": ScenarioPreset(
        id="inflationschock",
        name="Inflationschock (2023)",
        description="Surging inflation, rising rates, cost-of-living crisis. The hardest round in decades.",
        flavor_text=(
            "Inflation has surged past 10% for the first time since the 1990s. "
            "Energy prices, food costs, and mortgage rates are crushing households. "
            "Workers demand compensation for lost purchasing power. Employers warn "
            "that a wage-price spiral would be catastrophic. The Riksbank has raised "
            "rates aggressively. This is the most contentious round in a generation."
        ),
        parameters=MacroParameters(
            inflation=10.6,
            unemployment=7.5,
            gdp_growth=0.3,
            policy_rate=4.0,
            political_climate=4,
            export_pressure=ExportPressure.HIGH,
            previous_agreement=2.5,
        ),
    ),
    "90talskrisen": ScenarioPreset(
        id="90talskrisen",
        name="90-talskrisen",
        description="Deep recession, mass unemployment, fiscal emergency. Survival mode.",
        flavor_text=(
            "Sweden is in the worst economic crisis since the 1930s. Banks are failing, "
            "unemployment has tripled in two years, and the government is running massive "
            "deficits. The krona has been floated and is falling. There is a genuine fear "
            "that the Swedish model itself is at stake. Unions are on the defensive, "
            "employers push for structural reform."
        ),
        parameters=MacroParameters(
            inflation=4.5,
            unemployment=12.0,
            gdp_growth=-3.5,
            policy_rate=8.0,
            political_climate=4,
            export_pressure=ExportPressure.HIGH,
            previous_agreement=3.0,
        ),
    ),
    "hogkonjunktur": ScenarioPreset(
        id="hogkonjunktur",
        name="Högkonjunktur",
        description="Economic boom, labor shortage, record profits. Unions push hard.",
        flavor_text=(
            "The economy is overheating. Companies report record profits and can't find "
            "enough workers. Unemployment is at historic lows. Workers see their leverage "
            "and unions push for aggressive wage increases. Employers can afford it but "
            "worry about overheating and the Riksbank's reaction. The mood is confident "
            "but the stakes are high."
        ),
        parameters=MacroParameters(
            inflation=3.0,
            unemployment=3.5,
            gdp_growth=4.5,
            policy_rate=2.0,
            political_climate=2,
            export_pressure=ExportPressure.LOW,
            previous_agreement=2.8,
        ),
    ),
    "gron_omstallning": ScenarioPreset(
        id="gron_omstallning",
        name="Grön omställning",
        description="Green transition reshaping industries. New competence demands, structural upheaval.",
        flavor_text=(
            "The green transition is in full swing. Northern Sweden is booming with "
            "battery factories and green steel. Traditional industries face massive "
            "restructuring. The demand for skilled workers is enormous but in new areas. "
            "Unions want reskilling guarantees and transition security. Employers want "
            "flexibility to hire globally and restructure quickly. The old categories "
            "are breaking down."
        ),
        parameters=MacroParameters(
            inflation=2.5,
            unemployment=5.5,
            gdp_growth=3.0,
            policy_rate=2.0,
            political_climate=2,
            export_pressure=ExportPressure.MEDIUM,
            previous_agreement=2.5,
        ),
    ),
    "pandemi_aterhamtning": ScenarioPreset(
        id="pandemi_aterhamtning",
        name="Pandemiåterhämtning",
        description="Post-pandemic recovery. Private sector bounces back while public sector is exhausted and broke.",
        flavor_text=(
            "The pandemic is over but the scars remain. The private sector has recovered "
            "strongly — tech and manufacturing are booming. But the public sector is "
            "exhausted. Healthcare workers are burned out and leaving in droves. "
            "Municipal finances are strained after years of emergency spending. "
            "The gap between private and public sector working conditions has never "
            "been wider. Vårdförbundet is furious."
        ),
        parameters=MacroParameters(
            inflation=3.5,
            unemployment=8.0,
            gdp_growth=4.0,
            policy_rate=0.5,
            political_climate=3,
            export_pressure=ExportPressure.LOW,
            previous_agreement=2.0,
        ),
    ),
}
```

**Step 2: Verify**

```bash
cd backend && python -c "from app.scenarios.presets import PRESETS; print(f'{len(PRESETS)} presets loaded')"
# Expected: 6 presets loaded
```

**Step 3: Commit**

```bash
git add backend/app/scenarios/
git commit -m "feat: add 6 scenario presets with macro parameters and flavor text"
```

---

## Task 5: LLM Service

**Files:**
- Create: `backend/app/services/llm.py`

**Step 1: Write the Anthropic client wrapper**

```python
# backend/app/services/llm.py
import json
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def call_agent(system_prompt: str, user_prompt: str) -> dict:
    """Call Sonnet for agent reasoning. Returns parsed JSON."""
    response = await client.messages.create(
        model=settings.sonnet_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text
    # Extract JSON from response — handle markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse agent response: {text[:200]}")
        # Return a safe fallback
        return {
            "position": 0.0,
            "reasoning": "Failed to parse response",
            "public_statement": "No comment.",
            "willingness_to_settle": 50,
        }


async def call_summary(prompt: str) -> str:
    """Call Haiku for summaries."""
    response = await client.messages.create(
        model=settings.haiku_model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

**Step 2: Commit**

```bash
git add backend/app/services/llm.py
git commit -m "feat: add LLM service with Sonnet agent calls and Haiku summaries"
```

---

## Task 6: Agent Prompt System

**Files:**
- Create: `backend/app/agents/prompts.py`
- Create: `backend/app/agents/base.py`

**Step 1: Write prompt templates**

```python
# backend/app/agents/prompts.py

AGENT_SYSTEM_PROMPT = """You are {name}, {role_description}

You are participating in a Swedish avtalsrörelse (collective bargaining round).

YOUR PRIORITIES (ranked):
{priorities}

YOUR CONSTRAINTS:
{constraints}

IMPORTANT: You must respond with ONLY a JSON object (no markdown, no explanation outside the JSON):
{{
    "position": <your wage demand/offer as a percentage, e.g. 3.5>,
    "reasoning": "<your internal strategic reasoning, 2-3 sentences>",
    "public_statement": "<your public statement to media/other parties, 1-2 sentences in character>",
    "willingness_to_settle": <0-100, how ready you are to accept the current negotiation state>
}}
"""

AGENT_ROUND_PROMPT_OPENING = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%
- Riksbank policy rate: {policy_rate}%
- Political climate: {political_climate_desc}
- Export competitiveness pressure: {export_pressure}
- Previous agreement (märket): {previous_agreement}%

SCENARIO CONTEXT:
{flavor_text}

This is the OPENING ROUND. All parties are declaring their initial positions.
What is your opening demand/offer? Consider the macro environment and your institutional role.
Be realistic but strategic — your opening position should leave room for negotiation."""

AGENT_ROUND_PROMPT_NEGOTIATION = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%
- Riksbank policy rate: {policy_rate}%
- Political climate: {political_climate_desc}
- Export competitiveness pressure: {export_pressure}
- Previous agreement (märket): {previous_agreement}%

CURRENT NEGOTIATION STATE — Round {round_number}, Phase: {phase_name}
{marke_info}

OTHER PARTIES' CURRENT POSITIONS:
{other_positions}

NEGOTIATION HISTORY:
{history}

{special_context}

Decide your action this round. You may:
- Adjust your position (move toward or away from the other side)
- Hold firm
- Signal flexibility on specific issues
- Respond to other parties' statements

Consider the dynamics carefully. What serves your institutional mandate best right now?"""

MEDIATOR_PROMPT = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%

CURRENT NEGOTIATION STATE — Round {round_number}
The following negotiations are active:

{negotiation_status}

{stall_info}

As Medlingsinstitutet, assess the situation. If negotiations are stalled, you may:
- Propose a compromise figure
- Call for a cooling-off period
- Signal publicly that the parties need to move

Respond with JSON:
{{
    "position": <your proposed compromise figure if any, or 0 if not proposing>,
    "reasoning": "<your assessment of the situation>",
    "public_statement": "<your public communication>",
    "willingness_to_settle": <0-100, how close you think settlement is>
}}"""

CONFEDERATION_PROMPT = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%

CURRENT NEGOTIATION STATE — Round {round_number}, Phase: {phase_name}
{marke_info}

ALL PARTIES' POSITIONS:
{all_positions}

As {name}, you don't negotiate directly but you influence the round through coordination signals.
Assess the situation and issue guidance to your affiliates.

Respond with JSON:
{{
    "position": <your recommended target/ceiling as a percentage>,
    "reasoning": "<your strategic assessment>",
    "public_statement": "<your public coordination signal>",
    "willingness_to_settle": <0-100, how satisfied you are with the current trajectory>
}}"""

SUMMARY_PROMPT = """Summarize the following Swedish avtalsrörelse simulation results.

MACRO ENVIRONMENT:
- Inflation: {inflation}%, Unemployment: {unemployment}%, GDP growth: {gdp_growth}%

FINAL OUTCOMES:
{outcomes}

KEY EVENTS:
{events}

Write a compelling 3-4 paragraph summary in English covering:
1. The märket and how it was set
2. How other sectors followed (or deviated)
3. Key tensions, conflicts, and notable moments
4. Winners and losers — who got what they wanted?

Write in the style of a concise analytical briefing. Be specific about numbers."""


def format_political_climate(value: int) -> str:
    labels = {
        1: "Strongly left-leaning government (high public spending priority)",
        2: "Left-leaning government (supportive of unions)",
        3: "Centrist/balanced government",
        4: "Right-leaning government (business-friendly)",
        5: "Strongly right-leaning government (austerity-focused)",
    }
    return labels.get(value, "Centrist/balanced government")
```

**Step 2: Write the base agent class**

```python
# backend/app/agents/base.py
import asyncio
import logging

from app.agents.definitions import AGENTS
from app.agents.prompts import (
    AGENT_ROUND_PROMPT_NEGOTIATION,
    AGENT_ROUND_PROMPT_OPENING,
    AGENT_SYSTEM_PROMPT,
    CONFEDERATION_PROMPT,
    MEDIATOR_PROMPT,
    format_political_climate,
)
from app.models.agents import AgentAction, AgentState, AgentType
from app.models.scenario import MacroParameters
from app.models.simulation import Phase, SimulationState
from app.services.llm import call_agent

logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(self, agent_id: str, parameters: MacroParameters, flavor_text: str = ""):
        self.identity = AGENTS[agent_id]
        self.parameters = parameters
        self.flavor_text = flavor_text
        self.system_prompt = AGENT_SYSTEM_PROMPT.format(
            name=self.identity.name,
            role_description=self.identity.role_description,
            priorities="\n".join(f"  {i+1}. {p}" for i, p in enumerate(self.identity.priorities)),
            constraints="\n".join(f"  - {c}" for c in self.identity.constraints),
        )

    def _macro_params(self) -> dict:
        return {
            "inflation": self.parameters.inflation,
            "unemployment": self.parameters.unemployment,
            "gdp_growth": self.parameters.gdp_growth,
            "policy_rate": self.parameters.policy_rate,
            "political_climate_desc": format_political_climate(self.parameters.political_climate),
            "export_pressure": self.parameters.export_pressure.value,
            "previous_agreement": self.parameters.previous_agreement,
        }

    async def get_opening_action(self, round_number: int) -> AgentAction:
        prompt = AGENT_ROUND_PROMPT_OPENING.format(
            **self._macro_params(),
            flavor_text=self.flavor_text,
        )
        result = await call_agent(self.system_prompt, prompt)
        return AgentAction(
            agent_id=self.identity.id,
            round_number=round_number,
            phase=Phase.OPENING,
            position=float(result.get("position", 0)),
            reasoning=result.get("reasoning", ""),
            public_statement=result.get("public_statement", ""),
            willingness_to_settle=int(result.get("willingness_to_settle", 50)),
        )

    async def get_negotiation_action(
        self,
        sim: SimulationState,
        round_number: int,
        phase: Phase,
        other_positions: str,
        history: str,
        special_context: str = "",
    ) -> AgentAction:
        marke_info = ""
        if sim.marke is not None:
            marke_info = f"THE MÄRKET HAS BEEN SET AT {sim.marke}%. All agreements are expected to stay close to this level."

        phase_names = {
            Phase.INDUSTRIAVTALET: "Industriavtalet Negotiations",
            Phase.PRIVATE_SECTOR: "Private Sector Negotiations",
            Phase.PUBLIC_SECTOR: "Public Sector Negotiations",
        }

        if self.identity.agent_type == AgentType.MEDIATOR:
            prompt = MEDIATOR_PROMPT.format(
                **self._macro_params(),
                round_number=round_number,
                negotiation_status=other_positions,
                stall_info=special_context,
            )
        elif self.identity.agent_type == AgentType.CONFEDERATION:
            prompt = CONFEDERATION_PROMPT.format(
                inflation=self.parameters.inflation,
                unemployment=self.parameters.unemployment,
                gdp_growth=self.parameters.gdp_growth,
                round_number=round_number,
                phase_name=phase_names.get(phase, ""),
                marke_info=marke_info,
                all_positions=other_positions,
                name=self.identity.name,
            )
        else:
            prompt = AGENT_ROUND_PROMPT_NEGOTIATION.format(
                **self._macro_params(),
                round_number=round_number,
                phase_name=phase_names.get(phase, ""),
                marke_info=marke_info,
                other_positions=other_positions,
                history=history,
                special_context=special_context,
            )

        result = await call_agent(self.system_prompt, prompt)
        return AgentAction(
            agent_id=self.identity.id,
            round_number=round_number,
            phase=phase.value,
            position=float(result.get("position", 0)),
            reasoning=result.get("reasoning", ""),
            public_statement=result.get("public_statement", ""),
            willingness_to_settle=int(result.get("willingness_to_settle", 50)),
        )
```

**Step 3: Verify imports**

```bash
cd backend && python -c "from app.agents.base import AgentRunner; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/agents/
git commit -m "feat: add agent prompt system and AgentRunner with LLM integration"
```

---

## Task 7: Simulation Engine

**Files:**
- Create: `backend/app/engine/settlement.py`
- Create: `backend/app/engine/runner.py`

**Step 1: Write settlement logic**

```python
# backend/app/engine/settlement.py
from app.models.agents import AgentState
from app.models.simulation import ConflictEvent, NegotiationPair, SimulationState


def check_settlement(
    pair: NegotiationPair,
    agent_states: dict[str, AgentState],
) -> bool:
    """Check if both sides of a negotiation pair are ready to settle."""
    union_ready = all(
        agent_states[uid].willingness_to_settle >= 70 for uid in pair.union_ids
    )
    employer_ready = agent_states[pair.employer_id].willingness_to_settle >= 70
    return union_ready and employer_ready


def calculate_settlement_level(
    pair: NegotiationPair,
    agent_states: dict[str, AgentState],
) -> float:
    """Calculate the settlement level as a weighted average of positions."""
    union_positions = [agent_states[uid].current_position for uid in pair.union_ids]
    employer_position = agent_states[pair.employer_id].current_position
    avg_union = sum(p for p in union_positions if p is not None) / max(len([p for p in union_positions if p is not None]), 1)
    if employer_position is None:
        return avg_union
    # Settlement tends toward the middle, slightly weighted by willingness
    union_will = sum(agent_states[uid].willingness_to_settle for uid in pair.union_ids) / len(pair.union_ids)
    emp_will = agent_states[pair.employer_id].willingness_to_settle
    total_will = union_will + emp_will
    if total_will == 0:
        return (avg_union + employer_position) / 2
    # Higher willingness = more concession
    return (avg_union * emp_will + employer_position * union_will) / total_will


def check_conflict_events(
    agent_states: dict[str, AgentState],
    round_number: int,
    active_agent_ids: list[str],
) -> list[ConflictEvent]:
    """Check for strike/lockout threats based on low willingness."""
    events = []
    for agent_id in active_agent_ids:
        state = agent_states[agent_id]
        if state.willingness_to_settle < 40:
            state.rounds_at_low_willingness += 1
        else:
            state.rounds_at_low_willingness = 0

        if state.rounds_at_low_willingness >= 3 and not state.has_threatened_action:
            state.has_threatened_action = True
            from app.agents.definitions import AGENTS
            agent = AGENTS[agent_id]
            if agent.agent_type.value == "union":
                events.append(ConflictEvent(
                    event_type="strike_threat",
                    agent_id=agent_id,
                    round_number=round_number,
                    description=f"{agent.name} threatens industrial action if demands are not met.",
                ))
            elif agent.agent_type.value == "employer":
                events.append(ConflictEvent(
                    event_type="lockout_threat",
                    agent_id=agent_id,
                    round_number=round_number,
                    description=f"{agent.name} threatens lockout in response to union demands.",
                ))
    return events


def update_agent_state(state: AgentState, action) -> AgentState:
    """Update agent state from an action."""
    state.current_position = action.position
    state.willingness_to_settle = action.willingness_to_settle
    return state
```

**Step 2: Write the simulation runner**

```python
# backend/app/engine/runner.py
import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from app.agents.base import AgentRunner
from app.agents.definitions import AGENTS
from app.engine.settlement import (
    calculate_settlement_level,
    check_conflict_events,
    check_settlement,
    update_agent_state,
)
from app.models.agents import AgentAction, AgentState, AgentType
from app.models.scenario import MacroParameters
from app.models.simulation import (
    ConflictEvent,
    NegotiationPair,
    Phase,
    RoundResult,
    SimulationState,
)
from app.services.llm import call_summary
from app.agents.prompts import SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class SimulationRunner:
    def __init__(self, parameters: MacroParameters, preset_id: str | None = None, flavor_text: str = ""):
        self.sim = SimulationState(
            id=str(uuid.uuid4()),
            parameters=parameters,
            preset_id=preset_id,
        )
        self.flavor_text = flavor_text
        self.runners: dict[str, AgentRunner] = {}
        self._init_agents()
        self._init_negotiation_pairs()

    def _init_agents(self):
        for agent_id, identity in AGENTS.items():
            self.runners[agent_id] = AgentRunner(agent_id, self.sim.parameters, self.flavor_text)
            self.sim.agent_states[agent_id] = AgentState(agent_id=agent_id)

    def _init_negotiation_pairs(self):
        self.sim.negotiation_pairs = [
            # Industriavtalet
            NegotiationPair(union_ids=["if_metall", "unionen"], employer_id="teknikforetagen", phase=Phase.INDUSTRIAVTALET),
            # Private sector
            NegotiationPair(union_ids=["handels"], employer_id="svensk_handel", phase=Phase.PRIVATE_SECTOR),
            NegotiationPair(union_ids=["unionen"], employer_id="almega", phase=Phase.PRIVATE_SECTOR),
            # Public sector
            NegotiationPair(union_ids=["kommunal", "vision", "vardforbundet"], employer_id="skr", phase=Phase.PUBLIC_SECTOR),
        ]

    def _get_active_agents(self, phase: Phase) -> list[str]:
        """Get agent IDs active in this phase."""
        if phase == Phase.OPENING:
            return list(AGENTS.keys())

        tier_map = {
            Phase.INDUSTRIAVTALET: [1],  # Tier 1 negotiates
            Phase.PRIVATE_SECTOR: [2],   # Tier 2 negotiates
            Phase.PUBLIC_SECTOR: [3],    # Tier 3 negotiates
        }
        tiers = tier_map.get(phase, [])
        active = [aid for aid, a in AGENTS.items() if a.tier.value in tiers]
        # Always include confederations and mediator as observers/coordinators
        active.extend(aid for aid, a in AGENTS.items() if a.tier.value == 4)
        return active

    def _format_positions(self, agent_ids: list[str]) -> str:
        lines = []
        for aid in agent_ids:
            agent = AGENTS[aid]
            state = self.sim.agent_states[aid]
            pos = f"{state.current_position}%" if state.current_position is not None else "not yet declared"
            settled = " [SETTLED]" if state.is_settled else ""
            lines.append(f"- {agent.name} ({agent.agent_type.value}): {pos}{settled}")
        return "\n".join(lines)

    def _format_history(self, agent_id: str) -> str:
        lines = []
        for rnd in self.sim.rounds[-3:]:  # last 3 rounds
            for action in rnd.actions:
                if action.agent_id != agent_id:
                    agent = AGENTS[action.agent_id]
                    lines.append(f"Round {rnd.round_number}: {agent.name} — {action.public_statement}")
        return "\n".join(lines) if lines else "No history yet."

    def _check_phase_complete(self, phase: Phase) -> bool:
        """Check if all negotiation pairs for this phase are settled."""
        pairs = [p for p in self.sim.negotiation_pairs if p.phase == phase]
        return all(p.is_settled for p in pairs)

    async def run(self) -> AsyncGenerator[dict, None]:
        """Run the full simulation, yielding SSE events."""
        # Phase 1: Opening
        async for event in self._run_opening():
            yield event

        # Phase 2: Industriavtalet
        async for event in self._run_negotiation_phase(Phase.INDUSTRIAVTALET, max_rounds=6, stall_round=4):
            yield event

        # Phase 3: Private sector
        async for event in self._run_negotiation_phase(Phase.PRIVATE_SECTOR, max_rounds=4, stall_round=3):
            yield event

        # Phase 4: Public sector
        async for event in self._run_negotiation_phase(Phase.PUBLIC_SECTOR, max_rounds=4, stall_round=3):
            yield event

        # Phase 5: Summary
        async for event in self._run_summary():
            yield event

    async def _run_opening(self) -> AsyncGenerator[dict, None]:
        self.sim.current_phase = Phase.OPENING
        self.sim.current_round += 1
        round_num = self.sim.current_round

        yield {
            "event": "round_start",
            "data": {
                "round_number": round_num,
                "phase": Phase.OPENING.value,
                "phase_name": "Inledande krav",
                "active_agents": list(AGENTS.keys()),
            },
        }

        # All agents declare positions in parallel
        tasks = [self.runners[aid].get_opening_action(round_num) for aid in AGENTS]
        actions: list[AgentAction] = await asyncio.gather(*tasks)

        for action in actions:
            update_agent_state(self.sim.agent_states[action.agent_id], action)
            yield {"event": "agent_action", "data": action.model_dump()}

        round_result = RoundResult(
            round_number=round_num,
            phase=Phase.OPENING,
            actions=actions,
        )
        self.sim.rounds.append(round_result)

        yield {
            "event": "round_end",
            "data": {"round_number": round_num, "summary": "All parties have declared their opening positions."},
        }

    async def _run_negotiation_phase(
        self, phase: Phase, max_rounds: int, stall_round: int
    ) -> AsyncGenerator[dict, None]:
        self.sim.current_phase = phase
        phase_names = {
            Phase.INDUSTRIAVTALET: "Industriavtalet",
            Phase.PRIVATE_SECTOR: "Privat sektor",
            Phase.PUBLIC_SECTOR: "Offentlig sektor",
        }

        for r in range(max_rounds):
            self.sim.current_round += 1
            round_num = self.sim.current_round

            active_agents = self._get_active_agents(phase)
            # Filter out agents whose pairs are already settled
            active_agents = [
                aid for aid in active_agents
                if not self.sim.agent_states[aid].is_settled
            ]

            if not active_agents:
                break

            yield {
                "event": "round_start",
                "data": {
                    "round_number": round_num,
                    "phase": phase.value,
                    "phase_name": phase_names.get(phase, ""),
                    "active_agents": active_agents,
                },
            }

            # Build context for agents
            all_positions = self._format_positions(active_agents)
            special_context = ""
            if r >= stall_round:
                special_context = (
                    "NEGOTIATIONS ARE STALLING. Medlingsinstitutet is considering intervention. "
                    "Pressure to settle is mounting from all sides."
                )

            # Run all active agents in parallel
            tasks = []
            for aid in active_agents:
                history = self._format_history(aid)
                tasks.append(
                    self.runners[aid].get_negotiation_action(
                        self.sim, round_num, phase, all_positions, history, special_context
                    )
                )
            actions: list[AgentAction] = await asyncio.gather(*tasks)

            conflict_events = []
            for action in actions:
                update_agent_state(self.sim.agent_states[action.agent_id], action)
                yield {"event": "agent_action", "data": action.model_dump()}

            # Check for conflict events
            negotiating_ids = [
                aid for aid in active_agents
                if AGENTS[aid].agent_type in (AgentType.UNION, AgentType.EMPLOYER)
            ]
            conflict_events = check_conflict_events(
                self.sim.agent_states, round_num, negotiating_ids
            )
            for event in conflict_events:
                yield {"event": "conflict_event", "data": event.model_dump()}

            # Check settlements
            settlements = []
            for pair in self.sim.negotiation_pairs:
                if pair.phase == phase and not pair.is_settled:
                    if check_settlement(pair, self.sim.agent_states):
                        level = calculate_settlement_level(pair, self.sim.agent_states)
                        pair.is_settled = True
                        pair.settlement_level = round(level, 1)
                        pair.settlement_round = round_num
                        # Mark agents as settled
                        for uid in pair.union_ids:
                            self.sim.agent_states[uid].is_settled = True
                            self.sim.agent_states[uid].settlement_level = pair.settlement_level
                        self.sim.agent_states[pair.employer_id].is_settled = True
                        self.sim.agent_states[pair.employer_id].settlement_level = pair.settlement_level
                        # Set märket if this is industriavtalet
                        if phase == Phase.INDUSTRIAVTALET:
                            self.sim.marke = pair.settlement_level
                        settlements.append(pair)
                        yield {
                            "event": "settlement",
                            "data": {
                                "union_ids": pair.union_ids,
                                "employer_id": pair.employer_id,
                                "level": pair.settlement_level,
                                "round": round_num,
                            },
                        }

            round_result = RoundResult(
                round_number=round_num,
                phase=phase,
                actions=actions,
                settlements=[p.model_copy() for p in settlements],
                conflict_events=conflict_events,
            )
            self.sim.rounds.append(round_result)

            yield {
                "event": "round_end",
                "data": {"round_number": round_num, "summary": f"Round {round_num} complete."},
            }

            # Check if all pairs in this phase are settled
            if self._check_phase_complete(phase):
                break

        # Force settlement for any remaining unsettled pairs in this phase
        for pair in self.sim.negotiation_pairs:
            if pair.phase == phase and not pair.is_settled:
                level = calculate_settlement_level(pair, self.sim.agent_states)
                pair.is_settled = True
                pair.settlement_level = round(level, 1)
                pair.settlement_round = self.sim.current_round
                for uid in pair.union_ids:
                    self.sim.agent_states[uid].is_settled = True
                    self.sim.agent_states[uid].settlement_level = pair.settlement_level
                self.sim.agent_states[pair.employer_id].is_settled = True
                self.sim.agent_states[pair.employer_id].settlement_level = pair.settlement_level
                if phase == Phase.INDUSTRIAVTALET and self.sim.marke is None:
                    self.sim.marke = pair.settlement_level
                yield {
                    "event": "mediation",
                    "data": {
                        "description": f"Medlingsinstitutet brokers a settlement at {pair.settlement_level}%",
                        "union_ids": pair.union_ids,
                        "employer_id": pair.employer_id,
                        "level": pair.settlement_level,
                    },
                }

    async def _run_summary(self) -> AsyncGenerator[dict, None]:
        self.sim.current_phase = Phase.SUMMARY
        self.sim.is_complete = True

        outcomes = []
        for pair in self.sim.negotiation_pairs:
            union_names = ", ".join(AGENTS[uid].name for uid in pair.union_ids)
            emp_name = AGENTS[pair.employer_id].name
            outcomes.append(f"- {union_names} vs {emp_name}: settled at {pair.settlement_level}% (round {pair.settlement_round})")

        events_text = []
        for rnd in self.sim.rounds:
            for ce in rnd.conflict_events:
                events_text.append(f"- Round {ce.round_number}: {ce.description}")

        summary = await call_summary(SUMMARY_PROMPT.format(
            inflation=self.sim.parameters.inflation,
            unemployment=self.sim.parameters.unemployment,
            gdp_growth=self.sim.parameters.gdp_growth,
            outcomes="\n".join(outcomes),
            events="\n".join(events_text) if events_text else "No major conflict events.",
        ))

        self.sim.final_summary = summary

        yield {
            "event": "simulation_end",
            "data": {
                "summary": summary,
                "outcomes": [
                    {
                        "union_ids": p.union_ids,
                        "employer_id": p.employer_id,
                        "level": p.settlement_level,
                        "round": p.settlement_round,
                    }
                    for p in self.sim.negotiation_pairs
                ],
                "marke": self.sim.marke,
            },
        }
```

**Step 3: Verify imports**

```bash
cd backend && python -c "from app.engine.runner import SimulationRunner; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/engine/
git commit -m "feat: add simulation engine with round runner, settlement logic, and conflict detection"
```

---

## Task 8: API Routes & SSE Streaming

**Files:**
- Create: `backend/app/api/routes.py`
- Modify: `backend/app/main.py`

**Step 1: Write API routes**

```python
# backend/app/api/routes.py
import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.definitions import AGENTS
from app.engine.runner import SimulationRunner
from app.models.scenario import MacroParameters
from app.scenarios.presets import PRESETS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class SimulationRequest(BaseModel):
    preset_id: str | None = None
    parameters: MacroParameters | None = None


@router.get("/presets")
async def get_presets():
    return list(PRESETS.values())


@router.get("/agents")
async def get_agents():
    return list(AGENTS.values())


@router.post("/simulate")
async def simulate(request: SimulationRequest):
    # Determine parameters
    flavor_text = ""
    if request.preset_id:
        preset = PRESETS.get(request.preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{request.preset_id}' not found")
        parameters = request.parameters or preset.parameters
        flavor_text = preset.flavor_text
    elif request.parameters:
        parameters = request.parameters
    else:
        raise HTTPException(status_code=400, detail="Must provide preset_id or parameters")

    runner = SimulationRunner(parameters, request.preset_id, flavor_text)

    async def event_generator():
        async for event in runner.run():
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
```

**Step 2: Update main.py to include routes**

Add to `backend/app/main.py` after the middleware:

```python
from app.api.routes import router

app.include_router(router)
```

**Step 3: Verify server starts**

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
# Check http://localhost:8000/api/presets returns 6 presets
# Check http://localhost:8000/api/agents returns 13 agents
```

**Step 4: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add API routes with SSE simulation endpoint, presets, and agents list"
```

---

## Task 9: Frontend Project Scaffolding

**Files:**
- Create: `frontend/` (via Vite)
- Create: `frontend/src/types/index.ts`

**Step 1: Create Vite React TypeScript project**

```bash
cd /Users/nicklaslundblad/projects/avtalsrorelse
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
```

**Step 2: Configure Tailwind v4**

Update `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

Replace `frontend/src/index.css` with:
```css
@import "tailwindcss";

@theme {
  --color-swedish-blue: #006AA7;
  --color-swedish-blue-light: #E8F0F8;
  --color-swedish-gold: #FECC02;
  --color-swedish-gold-light: #FFF9E0;
  --color-settle-green: #16A34A;
  --color-firm-red: #DC2626;
  --color-flexible-yellow: #CA8A04;
  --font-sans: "Inter", system-ui, sans-serif;
}
```

**Step 3: Write TypeScript types**

```typescript
// frontend/src/types/index.ts

export type AgentType = "union" | "employer" | "confederation" | "mediator";
export type AgentTier = 1 | 2 | 3 | 4;
export type ExportPressure = "low" | "medium" | "high";
export type Relationship = "allied" | "opposed" | "neutral";

export interface MacroParameters {
  inflation: number;
  unemployment: number;
  gdp_growth: number;
  policy_rate: number;
  political_climate: number;
  export_pressure: ExportPressure;
  previous_agreement: number;
}

export interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  flavor_text: string;
  parameters: MacroParameters;
}

export interface AgentIdentity {
  id: string;
  name: string;
  short_name: string;
  agent_type: AgentType;
  tier: AgentTier;
  role_description: string;
  priorities: string[];
  constraints: string[];
  relationships: Record<string, Relationship>;
}

export interface AgentAction {
  agent_id: string;
  round_number: number;
  phase: number;
  position: number;
  reasoning: string;
  public_statement: string;
  willingness_to_settle: number;
}

export interface Settlement {
  union_ids: string[];
  employer_id: string;
  level: number;
  round: number;
}

export interface ConflictEvent {
  event_type: string;
  agent_id: string;
  round_number: number;
  description: string;
}

export interface RoundStart {
  round_number: number;
  phase: number;
  phase_name: string;
  active_agents: string[];
}

export interface RoundEnd {
  round_number: number;
  summary: string;
}

export interface SimulationEnd {
  summary: string;
  outcomes: Settlement[];
  marke: number | null;
}

export interface Mediation {
  description: string;
  union_ids: string[];
  employer_id: string;
  level: number;
}

// Frontend state
export interface AgentState {
  agent_id: string;
  current_position: number | null;
  willingness_to_settle: number;
  is_settled: boolean;
  settlement_level: number | null;
  actions: AgentAction[];
}

export type SimulationStatus = "idle" | "running" | "complete";
```

**Step 4: Clean up default Vite boilerplate**

Remove `src/App.css`, clear out the default content in `App.tsx`. Remove `src/assets/react.svg`.

**Step 5: Verify frontend runs**

```bash
cd frontend && npm run dev
# Should start on http://localhost:5173
```

**Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend with Vite, React, TypeScript, and TailwindCSS v4"
```

---

## Task 10: API Client & SSE Hook

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useSimulation.ts`

**Step 1: Write API client**

```typescript
// frontend/src/api/client.ts
import type { AgentIdentity, MacroParameters, ScenarioPreset } from "../types";

const BASE = "/api";

export async function fetchPresets(): Promise<ScenarioPreset[]> {
  const res = await fetch(`${BASE}/presets`);
  return res.json();
}

export async function fetchAgents(): Promise<AgentIdentity[]> {
  const res = await fetch(`${BASE}/agents`);
  return res.json();
}

export function startSimulation(
  presetId: string | null,
  parameters: MacroParameters | null,
): EventSource {
  const body = JSON.stringify({
    preset_id: presetId,
    parameters,
  });

  // Use fetch + ReadableStream for POST-based SSE
  // We'll use a custom EventSource-like approach
  const url = `${BASE}/simulate`;
  const eventSource = new EventSource(url + "?" + new URLSearchParams({
    // SSE via GET won't work for POST body, so we'll use fetchEventSource instead
  }));

  // Actually, we need a different approach since EventSource only supports GET.
  // We'll handle this in the hook.
  return eventSource;
}
```

Wait — EventSource only supports GET. We need to handle POST-based SSE differently. Let's update.

```typescript
// frontend/src/api/client.ts
import type { AgentIdentity, MacroParameters, ScenarioPreset } from "../types";

const BASE = "/api";

export async function fetchPresets(): Promise<ScenarioPreset[]> {
  const res = await fetch(`${BASE}/presets`);
  return res.json();
}

export async function fetchAgents(): Promise<AgentIdentity[]> {
  const res = await fetch(`${BASE}/agents`);
  return res.json();
}

export interface SSEEvent {
  event: string;
  data: string;
}

export async function* streamSimulation(
  presetId: string | null,
  parameters: MacroParameters | null,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset_id: presetId, parameters }),
  });

  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    let currentData = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        currentData = line.slice(5).trim();
      } else if (line === "" && currentEvent && currentData) {
        yield { event: currentEvent, data: currentData };
        currentEvent = "";
        currentData = "";
      }
    }
  }
}
```

**Step 2: Write the simulation hook**

```typescript
// frontend/src/hooks/useSimulation.ts
import { useCallback, useRef, useState } from "react";
import { streamSimulation } from "../api/client";
import type {
  AgentAction,
  AgentState,
  ConflictEvent,
  MacroParameters,
  Mediation,
  RoundStart,
  Settlement,
  SimulationEnd,
  SimulationStatus,
} from "../types";

export interface SimulationState {
  status: SimulationStatus;
  currentRound: number;
  currentPhase: number;
  currentPhaseName: string;
  agentStates: Record<string, AgentState>;
  settlements: Settlement[];
  conflictEvents: ConflictEvent[];
  mediations: Mediation[];
  actionFeed: AgentAction[];
  marke: number | null;
  finalSummary: string | null;
  outcomes: Settlement[];
}

const initialState: SimulationState = {
  status: "idle",
  currentRound: 0,
  currentPhase: 0,
  currentPhaseName: "",
  agentStates: {},
  settlements: [],
  conflictEvents: [],
  mediations: [],
  actionFeed: [],
  marke: null,
  finalSummary: null,
  outcomes: [],
};

export function useSimulation() {
  const [state, setState] = useState<SimulationState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(
    async (presetId: string | null, parameters: MacroParameters | null) => {
      setState({ ...initialState, status: "running" });

      try {
        for await (const event of streamSimulation(presetId, parameters)) {
          const data = JSON.parse(event.data);

          switch (event.event) {
            case "round_start": {
              const rs = data as RoundStart;
              setState((prev) => ({
                ...prev,
                currentRound: rs.round_number,
                currentPhase: rs.phase,
                currentPhaseName: rs.phase_name,
              }));
              break;
            }

            case "agent_action": {
              const action = data as AgentAction;
              setState((prev) => {
                const agentState = prev.agentStates[action.agent_id] || {
                  agent_id: action.agent_id,
                  current_position: null,
                  willingness_to_settle: 50,
                  is_settled: false,
                  settlement_level: null,
                  actions: [],
                };
                return {
                  ...prev,
                  agentStates: {
                    ...prev.agentStates,
                    [action.agent_id]: {
                      ...agentState,
                      current_position: action.position,
                      willingness_to_settle: action.willingness_to_settle,
                      actions: [...agentState.actions, action],
                    },
                  },
                  actionFeed: [...prev.actionFeed, action],
                };
              });
              break;
            }

            case "settlement": {
              const s = data as Settlement;
              setState((prev) => {
                const updated = { ...prev, settlements: [...prev.settlements, s] };
                // Mark agents as settled
                for (const uid of s.union_ids) {
                  if (updated.agentStates[uid]) {
                    updated.agentStates[uid] = {
                      ...updated.agentStates[uid],
                      is_settled: true,
                      settlement_level: s.level,
                    };
                  }
                }
                if (updated.agentStates[s.employer_id]) {
                  updated.agentStates[s.employer_id] = {
                    ...updated.agentStates[s.employer_id],
                    is_settled: true,
                    settlement_level: s.level,
                  };
                }
                return updated;
              });
              break;
            }

            case "conflict_event": {
              const ce = data as ConflictEvent;
              setState((prev) => ({
                ...prev,
                conflictEvents: [...prev.conflictEvents, ce],
              }));
              break;
            }

            case "mediation": {
              const m = data as Mediation;
              setState((prev) => ({
                ...prev,
                mediations: [...prev.mediations, m],
              }));
              break;
            }

            case "simulation_end": {
              const end = data as SimulationEnd;
              setState((prev) => ({
                ...prev,
                status: "complete",
                marke: end.marke,
                finalSummary: end.summary,
                outcomes: end.outcomes,
              }));
              break;
            }
          }
        }
      } catch (error) {
        console.error("Simulation error:", error);
        setState((prev) => ({ ...prev, status: "idle" }));
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { state, start, reset };
}
```

**Step 3: Commit**

```bash
git add frontend/src/api/ frontend/src/hooks/
git commit -m "feat: add API client with SSE streaming and useSimulation hook"
```

---

## Task 11: Setup Page

**Files:**
- Create: `frontend/src/pages/SetupPage.tsx`
- Create: `frontend/src/components/setup/PresetCard.tsx`
- Create: `frontend/src/components/setup/ParameterSliders.tsx`
- Create: `frontend/src/components/setup/AgentRoster.tsx`

**Step 1: Write PresetCard component**

```tsx
// frontend/src/components/setup/PresetCard.tsx
import type { ScenarioPreset } from "../../types";

const PRESET_ICONS: Record<string, string> = {
  stabil_tillvaxt: "⚖️",
  inflationschock: "📈",
  "90talskrisen": "📉",
  hogkonjunktur: "🚀",
  gron_omstallning: "🌿",
  pandemi_aterhamtning: "🏥",
};

interface Props {
  preset: ScenarioPreset;
  selected: boolean;
  onSelect: () => void;
}

export function PresetCard({ preset, selected, onSelect }: Props) {
  return (
    <button
      onClick={onSelect}
      className={`text-left p-5 rounded-xl border-2 transition-all duration-200 cursor-pointer
        ${selected
          ? "border-swedish-blue bg-swedish-blue-light shadow-md"
          : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
        }`}
    >
      <div className="text-2xl mb-2">{PRESET_ICONS[preset.id] || "📊"}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{preset.name}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{preset.description}</p>
    </button>
  );
}
```

**Step 2: Write ParameterSliders component**

```tsx
// frontend/src/components/setup/ParameterSliders.tsx
import type { ExportPressure, MacroParameters } from "../../types";

interface Props {
  parameters: MacroParameters;
  onChange: (params: MacroParameters) => void;
}

interface SliderConfig {
  key: keyof MacroParameters;
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
}

const SLIDERS: SliderConfig[] = [
  { key: "inflation", label: "Inflation (KPI)", min: 0, max: 15, step: 0.1, unit: "%" },
  { key: "unemployment", label: "Arbetslöshet", min: 2, max: 15, step: 0.1, unit: "%" },
  { key: "gdp_growth", label: "BNP-tillväxt", min: -5, max: 8, step: 0.1, unit: "%" },
  { key: "policy_rate", label: "Styrränta", min: -0.5, max: 10, step: 0.25, unit: "%" },
  { key: "previous_agreement", label: "Tidigare märke", min: 0, max: 8, step: 0.1, unit: "%" },
];

const POLITICAL_LABELS = ["", "Vänster", "Mittvänster", "Mitten", "Mitterhöger", "Höger"];

export function ParameterSliders({ parameters, onChange }: Props) {
  const update = (key: string, value: number | string) => {
    onChange({ ...parameters, [key]: value });
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-900">Makroparametrar</h3>

      {SLIDERS.map((s) => (
        <div key={s.key}>
          <div className="flex justify-between text-sm mb-1">
            <label className="text-gray-700">{s.label}</label>
            <span className="font-mono text-gray-900">
              {(parameters[s.key] as number).toFixed(1)}{s.unit}
            </span>
          </div>
          <input
            type="range"
            min={s.min}
            max={s.max}
            step={s.step}
            value={parameters[s.key] as number}
            onChange={(e) => update(s.key, parseFloat(e.target.value))}
            className="w-full accent-swedish-blue"
          />
        </div>
      ))}

      <div>
        <div className="flex justify-between text-sm mb-1">
          <label className="text-gray-700">Politiskt klimat</label>
          <span className="font-mono text-gray-900">
            {POLITICAL_LABELS[parameters.political_climate]}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={parameters.political_climate}
          onChange={(e) => update("political_climate", parseInt(e.target.value))}
          className="w-full accent-swedish-blue"
        />
      </div>

      <div>
        <label className="text-sm text-gray-700 block mb-1">Exporttryck</label>
        <div className="flex gap-2">
          {(["low", "medium", "high"] as ExportPressure[]).map((level) => (
            <button
              key={level}
              onClick={() => update("export_pressure", level)}
              className={`px-3 py-1 rounded-md text-sm transition-colors ${
                parameters.export_pressure === level
                  ? "bg-swedish-blue text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {level === "low" ? "Lågt" : level === "medium" ? "Medel" : "Högt"}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Step 3: Write AgentRoster component**

```tsx
// frontend/src/components/setup/AgentRoster.tsx
import type { AgentIdentity } from "../../types";

const TYPE_COLORS: Record<string, string> = {
  union: "bg-blue-100 text-blue-800",
  employer: "bg-amber-100 text-amber-800",
  confederation: "bg-purple-100 text-purple-800",
  mediator: "bg-green-100 text-green-800",
};

const TYPE_LABELS: Record<string, string> = {
  union: "Fackförbund",
  employer: "Arbetsgivare",
  confederation: "Centralorganisation",
  mediator: "Medlare",
};

const TIER_LABELS: Record<number, string> = {
  1: "Normerande (Industrin)",
  2: "Privat sektor",
  3: "Offentlig sektor",
  4: "Samordning",
};

interface Props {
  agents: AgentIdentity[];
}

export function AgentRoster({ agents }: Props) {
  const tiers = [1, 2, 3, 4] as const;

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-900">Aktörer</h3>
      {tiers.map((tier) => {
        const tierAgents = agents.filter((a) => a.tier === tier);
        if (tierAgents.length === 0) return null;
        return (
          <div key={tier}>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              {TIER_LABELS[tier]}
            </p>
            <div className="flex flex-wrap gap-2">
              {tierAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-50 border border-gray-200"
                >
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${TYPE_COLORS[agent.agent_type]}`}>
                    {TYPE_LABELS[agent.agent_type]}
                  </span>
                  <span className="text-sm text-gray-800">{agent.short_name}</span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

**Step 4: Write SetupPage**

```tsx
// frontend/src/pages/SetupPage.tsx
import { useEffect, useState } from "react";
import { fetchAgents, fetchPresets } from "../api/client";
import { AgentRoster } from "../components/setup/AgentRoster";
import { ParameterSliders } from "../components/setup/ParameterSliders";
import { PresetCard } from "../components/setup/PresetCard";
import type { AgentIdentity, MacroParameters, ScenarioPreset } from "../types";

interface Props {
  onStart: (presetId: string | null, parameters: MacroParameters) => void;
}

export function SetupPage({ onStart }: Props) {
  const [presets, setPresets] = useState<ScenarioPreset[]>([]);
  const [agents, setAgents] = useState<AgentIdentity[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [parameters, setParameters] = useState<MacroParameters>({
    inflation: 2.0,
    unemployment: 7.0,
    gdp_growth: 2.0,
    policy_rate: 2.5,
    political_climate: 3,
    export_pressure: "medium",
    previous_agreement: 2.5,
  });

  useEffect(() => {
    fetchPresets().then(setPresets);
    fetchAgents().then(setAgents);
  }, []);

  const handlePresetSelect = (preset: ScenarioPreset) => {
    setSelectedPreset(preset.id);
    setParameters(preset.parameters);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Avtalsrörelsen</h1>
          <p className="text-gray-600 mt-1">Simulering av svensk lönebildning</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Scenario presets */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Välj scenario</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {presets.map((preset) => (
              <PresetCard
                key={preset.id}
                preset={preset}
                selected={selectedPreset === preset.id}
                onSelect={() => handlePresetSelect(preset)}
              />
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Parameters */}
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <ParameterSliders parameters={parameters} onChange={setParameters} />
          </section>

          {/* Agent roster */}
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <AgentRoster agents={agents} />
          </section>
        </div>

        {/* Launch button */}
        <div className="flex justify-center pt-4">
          <button
            onClick={() => onStart(selectedPreset, parameters)}
            className="px-8 py-3 bg-swedish-blue text-white rounded-xl font-semibold text-lg
                     hover:bg-swedish-blue/90 transition-colors shadow-sm hover:shadow-md
                     active:scale-[0.98] cursor-pointer"
          >
            Starta förhandling
          </button>
        </div>
      </main>
    </div>
  );
}
```

**Step 5: Commit**

```bash
git add frontend/src/pages/SetupPage.tsx frontend/src/components/setup/
git commit -m "feat: add setup page with preset cards, parameter sliders, and agent roster"
```

---

## Task 12: War Room — Agent Panel (Left Column)

**Files:**
- Create: `frontend/src/components/warroom/AgentCard.tsx`
- Create: `frontend/src/components/warroom/AgentPanel.tsx`

**Step 1: Write AgentCard**

```tsx
// frontend/src/components/warroom/AgentCard.tsx
import { useState } from "react";
import type { AgentIdentity, AgentState } from "../../types";

interface Props {
  identity: AgentIdentity;
  state: AgentState | undefined;
}

const TYPE_BADGE: Record<string, { label: string; class: string }> = {
  union: { label: "Fack", class: "bg-blue-100 text-blue-700" },
  employer: { label: "AG", class: "bg-amber-100 text-amber-700" },
  confederation: { label: "CO", class: "bg-purple-100 text-purple-700" },
  mediator: { label: "MI", class: "bg-green-100 text-green-700" },
};

function sentimentColor(willingness: number): string {
  if (willingness >= 70) return "bg-settle-green";
  if (willingness >= 40) return "bg-flexible-yellow";
  return "bg-firm-red";
}

export function AgentCard({ identity, state }: Props) {
  const [expanded, setExpanded] = useState(false);
  const badge = TYPE_BADGE[identity.agent_type];
  const position = state?.current_position;
  const willingness = state?.willingness_to_settle ?? 50;
  const lastAction = state?.actions[state.actions.length - 1];

  return (
    <div
      className={`rounded-lg border transition-all duration-300 cursor-pointer
        ${state?.is_settled
          ? "border-settle-green/30 bg-settle-green/5"
          : "border-gray-200 bg-white hover:border-gray-300"
        }`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="p-3">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${badge.class}`}>
              {badge.label}
            </span>
            <span className="text-sm font-semibold text-gray-900">{identity.short_name}</span>
          </div>
          {position !== null && position !== undefined && (
            <span className="text-lg font-bold text-gray-900 font-mono">
              {position.toFixed(1)}%
            </span>
          )}
        </div>

        {state?.is_settled && state.settlement_level !== null && (
          <div className="text-xs text-settle-green font-medium mb-1.5">
            Avtal: {state.settlement_level}%
          </div>
        )}

        {/* Willingness bar */}
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${sentimentColor(willingness)}`}
            style={{ width: `${willingness}%` }}
          />
        </div>
      </div>

      {/* Expanded content */}
      {expanded && lastAction && (
        <div className="px-3 pb-3 border-t border-gray-100 mt-1 pt-2 space-y-2">
          <div>
            <p className="text-[10px] uppercase text-gray-500 font-medium">Intern analys</p>
            <p className="text-xs text-gray-700 leading-relaxed">{lastAction.reasoning}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-gray-500 font-medium">Offentligt uttalande</p>
            <p className="text-xs text-gray-700 italic leading-relaxed">"{lastAction.public_statement}"</p>
          </div>
          <div className="flex justify-between text-[10px] text-gray-500">
            <span>Förhandlingsvilja: {willingness}/100</span>
            <span>Omgång {lastAction.round_number}</span>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Write AgentPanel**

```tsx
// frontend/src/components/warroom/AgentPanel.tsx
import type { AgentIdentity, AgentState } from "../../types";
import { AgentCard } from "./AgentCard";

const TIER_LABELS: Record<number, string> = {
  1: "Industrin",
  2: "Privat sektor",
  3: "Offentlig sektor",
  4: "Samordning",
};

interface Props {
  agents: AgentIdentity[];
  agentStates: Record<string, AgentState>;
}

export function AgentPanel({ agents, agentStates }: Props) {
  const tiers = [1, 2, 3, 4] as const;

  return (
    <div className="h-full overflow-y-auto space-y-4 pr-1">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Aktörer</h2>
      {tiers.map((tier) => {
        const tierAgents = agents.filter((a) => a.tier === tier);
        if (tierAgents.length === 0) return null;
        return (
          <div key={tier}>
            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1.5">
              {TIER_LABELS[tier]}
            </p>
            <div className="space-y-1.5">
              {tierAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  identity={agent}
                  state={agentStates[agent.id]}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/warroom/AgentCard.tsx frontend/src/components/warroom/AgentPanel.tsx
git commit -m "feat: add war room agent panel with expandable agent cards and sentiment indicators"
```

---

## Task 13: War Room — Center Stage

**Files:**
- Create: `frontend/src/components/warroom/RoundHeader.tsx`
- Create: `frontend/src/components/warroom/ActionFeed.tsx`
- Create: `frontend/src/components/warroom/CenterStage.tsx`

**Step 1: Write RoundHeader**

```tsx
// frontend/src/components/warroom/RoundHeader.tsx
interface Props {
  round: number;
  phase: number;
  phaseName: string;
  status: "idle" | "running" | "complete";
}

const PHASE_COUNT = 5;

export function RoundHeader({ round, phase, phaseName, status }: Props) {
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            {status === "complete" ? "Förhandling avslutad" : phaseName || "Väntar..."}
          </h2>
          {status === "running" && (
            <p className="text-sm text-gray-500">Omgång {round}</p>
          )}
        </div>
        {status === "running" && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-swedish-blue rounded-full animate-pulse" />
            <span className="text-xs text-gray-500">Pågår</span>
          </div>
        )}
      </div>

      {/* Phase progress */}
      <div className="flex gap-1">
        {Array.from({ length: PHASE_COUNT }, (_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              i + 1 < phase
                ? "bg-swedish-blue"
                : i + 1 === phase
                  ? "bg-swedish-blue/60"
                  : "bg-gray-200"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Write ActionFeed**

```tsx
// frontend/src/components/warroom/ActionFeed.tsx
import { useEffect, useRef } from "react";
import type { AgentAction, AgentIdentity, ConflictEvent } from "../../types";

type FeedItem =
  | { type: "action"; data: AgentAction }
  | { type: "conflict"; data: ConflictEvent };

interface Props {
  actions: AgentAction[];
  conflictEvents: ConflictEvent[];
  agents: Record<string, AgentIdentity>;
}

export function ActionFeed({ actions, conflictEvents, agents }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Merge and sort by round
  const feed: FeedItem[] = [
    ...actions.map((a) => ({ type: "action" as const, data: a })),
    ...conflictEvents.map((c) => ({ type: "conflict" as const, data: c })),
  ].sort((a, b) => {
    const rA = a.type === "action" ? a.data.round_number : a.data.round_number;
    const rB = b.type === "action" ? b.data.round_number : b.data.round_number;
    return rA - rB;
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [feed.length]);

  return (
    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
      {feed.map((item, i) => {
        if (item.type === "conflict") {
          return (
            <div
              key={`conflict-${i}`}
              className="p-3 rounded-lg bg-firm-red/5 border border-firm-red/20 animate-in fade-in"
            >
              <p className="text-sm font-semibold text-firm-red">{item.data.description}</p>
            </div>
          );
        }

        const agent = agents[item.data.agent_id];
        if (!agent) return null;

        return (
          <div
            key={`action-${i}`}
            className="p-3 rounded-lg bg-white border border-gray-100 shadow-sm animate-in fade-in"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-gray-900">{agent.short_name}</span>
              <span className="text-[10px] text-gray-400">Omgång {item.data.round_number}</span>
            </div>
            <p className="text-sm text-gray-700 italic">"{item.data.public_statement}"</p>
            <div className="flex items-center gap-3 mt-1.5">
              <span className="text-xs font-mono text-gray-600">
                Position: {item.data.position.toFixed(1)}%
              </span>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-600">
                Vilja: {item.data.willingness_to_settle}/100
              </span>
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
```

**Step 3: Write CenterStage**

```tsx
// frontend/src/components/warroom/CenterStage.tsx
import type { AgentAction, AgentIdentity, ConflictEvent } from "../../types";
import { ActionFeed } from "./ActionFeed";
import { RoundHeader } from "./RoundHeader";

interface Props {
  round: number;
  phase: number;
  phaseName: string;
  status: "idle" | "running" | "complete";
  actions: AgentAction[];
  conflictEvents: ConflictEvent[];
  agents: Record<string, AgentIdentity>;
  finalSummary: string | null;
}

export function CenterStage({
  round,
  phase,
  phaseName,
  status,
  actions,
  conflictEvents,
  agents,
  finalSummary,
}: Props) {
  return (
    <div className="h-full flex flex-col">
      <RoundHeader round={round} phase={phase} phaseName={phaseName} status={status} />

      {finalSummary ? (
        <div className="flex-1 overflow-y-auto">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Sammanfattning</h3>
            <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {finalSummary}
            </div>
          </div>
        </div>
      ) : (
        <ActionFeed actions={actions} conflictEvents={conflictEvents} agents={agents} />
      )}
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/warroom/RoundHeader.tsx frontend/src/components/warroom/ActionFeed.tsx frontend/src/components/warroom/CenterStage.tsx
git commit -m "feat: add war room center stage with round header, action feed, and summary view"
```

---

## Task 14: War Room — Info Panel (Right Column)

**Files:**
- Create: `frontend/src/components/warroom/MacroSummary.tsx`
- Create: `frontend/src/components/warroom/SettlementTracker.tsx`
- Create: `frontend/src/components/warroom/InfoPanel.tsx`

**Step 1: Write MacroSummary**

```tsx
// frontend/src/components/warroom/MacroSummary.tsx
import type { MacroParameters } from "../../types";

interface Props {
  parameters: MacroParameters;
  marke: number | null;
}

export function MacroSummary({ parameters, marke }: Props) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Makro</h3>

      {marke !== null && (
        <div className="p-3 rounded-lg bg-swedish-gold-light border border-swedish-gold/30">
          <p className="text-[10px] uppercase text-gray-500 font-medium">Märket</p>
          <p className="text-2xl font-bold text-gray-900 font-mono">{marke}%</p>
        </div>
      )}

      <div className="space-y-1.5">
        {[
          { label: "Inflation", value: `${parameters.inflation.toFixed(1)}%` },
          { label: "Arbetslöshet", value: `${parameters.unemployment.toFixed(1)}%` },
          { label: "BNP-tillväxt", value: `${parameters.gdp_growth.toFixed(1)}%` },
          { label: "Styrränta", value: `${parameters.policy_rate.toFixed(1)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="flex justify-between text-xs">
            <span className="text-gray-500">{label}</span>
            <span className="font-mono text-gray-800">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Write SettlementTracker**

```tsx
// frontend/src/components/warroom/SettlementTracker.tsx
import type { AgentIdentity, Settlement } from "../../types";

interface NegotiationPairDef {
  label: string;
  union_ids: string[];
  employer_id: string;
}

const PAIRS: NegotiationPairDef[] = [
  { label: "Industriavtalet", union_ids: ["if_metall", "unionen"], employer_id: "teknikforetagen" },
  { label: "Handels – Sv Handel", union_ids: ["handels"], employer_id: "svensk_handel" },
  { label: "Unionen – Almega", union_ids: ["unionen"], employer_id: "almega" },
  { label: "Offentlig sektor", union_ids: ["kommunal", "vision", "vardforbundet"], employer_id: "skr" },
];

interface Props {
  settlements: Settlement[];
  agents: Record<string, AgentIdentity>;
}

export function SettlementTracker({ settlements }: Props) {
  const isSettled = (pair: NegotiationPairDef): Settlement | undefined => {
    return settlements.find(
      (s) => s.employer_id === pair.employer_id && s.union_ids.some((u) => pair.union_ids.includes(u)),
    );
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Avtal</h3>
      <div className="space-y-2">
        {PAIRS.map((pair) => {
          const settlement = isSettled(pair);
          return (
            <div
              key={pair.label}
              className={`flex items-center justify-between p-2 rounded-lg border transition-colors ${
                settlement
                  ? "border-settle-green/30 bg-settle-green/5"
                  : "border-gray-100 bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full border-2 transition-colors ${
                    settlement ? "bg-settle-green border-settle-green" : "border-gray-300"
                  }`}
                />
                <span className="text-xs text-gray-700">{pair.label}</span>
              </div>
              {settlement && (
                <span className="text-xs font-bold font-mono text-settle-green">
                  {settlement.level}%
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**Step 3: Write InfoPanel**

```tsx
// frontend/src/components/warroom/InfoPanel.tsx
import type { AgentIdentity, MacroParameters, Settlement } from "../../types";
import { MacroSummary } from "./MacroSummary";
import { SettlementTracker } from "./SettlementTracker";

interface Props {
  parameters: MacroParameters;
  marke: number | null;
  settlements: Settlement[];
  agents: Record<string, AgentIdentity>;
}

export function InfoPanel({ parameters, marke, settlements, agents }: Props) {
  return (
    <div className="h-full overflow-y-auto space-y-6 pl-1">
      <MacroSummary parameters={parameters} marke={marke} />
      <SettlementTracker settlements={settlements} agents={agents} />
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/warroom/MacroSummary.tsx frontend/src/components/warroom/SettlementTracker.tsx frontend/src/components/warroom/InfoPanel.tsx
git commit -m "feat: add war room info panel with macro summary and settlement tracker"
```

---

## Task 15: War Room Page & App Assembly

**Files:**
- Create: `frontend/src/pages/SimulationPage.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write SimulationPage**

```tsx
// frontend/src/pages/SimulationPage.tsx
import { useMemo } from "react";
import type { AgentIdentity, MacroParameters } from "../types";
import type { SimulationState } from "../hooks/useSimulation";
import { AgentPanel } from "../components/warroom/AgentPanel";
import { CenterStage } from "../components/warroom/CenterStage";
import { InfoPanel } from "../components/warroom/InfoPanel";

interface Props {
  agents: AgentIdentity[];
  parameters: MacroParameters;
  simulation: SimulationState;
  onBack: () => void;
}

export function SimulationPage({ agents, parameters, simulation, onBack }: Props) {
  const agentMap = useMemo(
    () => Object.fromEntries(agents.map((a) => [a.id, a])),
    [agents],
  );

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top bar */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="text-sm text-gray-500 hover:text-gray-800 transition-colors cursor-pointer"
          >
            &larr; Tillbaka
          </button>
          <h1 className="text-lg font-bold text-gray-900">Avtalsrörelsen</h1>
        </div>
        {simulation.status === "running" && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-swedish-blue rounded-full animate-pulse" />
            <span className="text-sm text-gray-500">Simulering pågår...</span>
          </div>
        )}
      </header>

      {/* Three-column layout */}
      <div className="flex-1 grid grid-cols-[280px_1fr_260px] gap-4 p-4 min-h-0">
        {/* Left: Agent panel */}
        <div className="min-h-0 overflow-hidden">
          <AgentPanel agents={agents} agentStates={simulation.agentStates} />
        </div>

        {/* Center: Action feed */}
        <div className="min-h-0 overflow-hidden">
          <CenterStage
            round={simulation.currentRound}
            phase={simulation.currentPhase}
            phaseName={simulation.currentPhaseName}
            status={simulation.status}
            actions={simulation.actionFeed}
            conflictEvents={simulation.conflictEvents}
            agents={agentMap}
            finalSummary={simulation.finalSummary}
          />
        </div>

        {/* Right: Info panel */}
        <div className="min-h-0 overflow-hidden">
          <InfoPanel
            parameters={parameters}
            marke={simulation.marke}
            settlements={simulation.settlements}
            agents={agentMap}
          />
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Write App.tsx**

```tsx
// frontend/src/App.tsx
import { useEffect, useState } from "react";
import { fetchAgents } from "./api/client";
import { useSimulation } from "./hooks/useSimulation";
import { SetupPage } from "./pages/SetupPage";
import { SimulationPage } from "./pages/SimulationPage";
import type { AgentIdentity, MacroParameters } from "./types";

type View = "setup" | "simulation";

export default function App() {
  const [view, setView] = useState<View>("setup");
  const [agents, setAgents] = useState<AgentIdentity[]>([]);
  const [activeParams, setActiveParams] = useState<MacroParameters | null>(null);
  const { state: simulation, start, reset } = useSimulation();

  useEffect(() => {
    fetchAgents().then(setAgents);
  }, []);

  const handleStart = async (presetId: string | null, parameters: MacroParameters) => {
    setActiveParams(parameters);
    setView("simulation");
    await start(presetId, parameters);
  };

  const handleBack = () => {
    reset();
    setView("setup");
  };

  if (view === "simulation" && activeParams) {
    return (
      <SimulationPage
        agents={agents}
        parameters={activeParams}
        simulation={simulation}
        onBack={handleBack}
      />
    );
  }

  return <SetupPage onStart={handleStart} />;
}
```

**Step 3: Verify frontend compiles**

```bash
cd frontend && npm run build
```

**Step 4: Commit**

```bash
git add frontend/src/pages/SimulationPage.tsx frontend/src/App.tsx
git commit -m "feat: add simulation page with three-column war room layout and app routing"
```

---

## Task 16: Railway Deployment Config

**Files:**
- Create: `backend/Procfile`
- Create: `backend/railway.json`
- Create: `frontend/railway.json`
- Create: `railway.toml` (root, optional — for monorepo config)
- Modify: `backend/app/config.py` — add production CORS

**Step 1: Backend deployment files**

```
# backend/Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

```json
// backend/railway.json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Step 2: Update config.py for production CORS**

Update the `cors_origins` default in `backend/app/config.py`:

```python
cors_origins: list[str] = ["http://localhost:5173", "https://*.up.railway.app"]
```

And update the CORS middleware in `main.py` to use `allow_origin_regex` for Railway wildcard:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 3: Frontend deployment**

The frontend needs to be built and served statically, with the API URL pointing to the backend service.

Create `frontend/railway.json`:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npx serve dist -s -l ${PORT:-3000}"
  }
}
```

Add `serve` to frontend dev deps:
```bash
cd frontend && npm install --save-dev serve
```

Update `frontend/src/api/client.ts` to use an env variable for the API base:
```typescript
const BASE = import.meta.env.VITE_API_URL || "/api";
```

And update `frontend/vite.config.ts` proxy to only apply in dev.

**Step 4: Create root .gitignore**

```
# backend
backend/.venv/
backend/.env
__pycache__/
*.pyc

# frontend
frontend/node_modules/
frontend/dist/

# IDE
.idea/
.vscode/
*.swp
.DS_Store
```

**Step 5: Commit**

```bash
git add backend/Procfile backend/railway.json frontend/railway.json .gitignore backend/app/config.py backend/app/main.py frontend/src/api/client.ts
git commit -m "feat: add Railway deployment configuration for backend and frontend services"
```

---

## Task 17: End-to-End Smoke Test

**Step 1: Start backend**

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

**Step 2: Start frontend**

```bash
cd frontend && npm run dev
```

**Step 3: Manual test flow**

1. Open http://localhost:5173
2. Verify preset cards load and are clickable
3. Verify parameter sliders update when preset is selected
4. Verify agent roster shows 13 agents
5. Select "Inflationschock" preset
6. Click "Starta förhandling"
7. Verify SSE stream starts — agent actions appear in center feed
8. Verify agent cards update with positions and willingness
9. Verify settlements appear in the right panel tracker
10. Wait for simulation to complete — verify final summary renders

**Step 4: Fix any issues found during smoke test**

**Step 5: Final commit**

```bash
git add -A
git commit -m "fix: address smoke test issues"
```

---

## Task 18: Deploy to Railway

**Step 1: Create Railway project**

```bash
# Install Railway CLI if not present
brew install railway

# Login
railway login

# Create project
railway init
```

**Step 2: Deploy backend service**

```bash
cd backend
railway up
# Set env var
railway variables set ANTHROPIC_API_KEY=<your-key>
```

**Step 3: Deploy frontend service**

```bash
cd frontend
# Set the API URL to the backend service URL
railway variables set VITE_API_URL=https://<backend-service>.up.railway.app/api
railway up
```

**Step 4: Verify production**

Open the frontend Railway URL and run through the same smoke test as Task 17.

**Step 5: Commit any deployment fixes**

```bash
git add -A && git commit -m "fix: deployment configuration adjustments"
```

---

## Summary

18 tasks total:
- Tasks 1-8: Backend (scaffolding, models, agents, scenarios, LLM, prompts, engine, API)
- Tasks 9-15: Frontend (scaffolding, types, API client, setup page, war room components, assembly)
- Task 16: Railway deployment config
- Task 17: Smoke test
- Task 18: Deploy

Estimated LLM calls per simulation run: ~50-80 (13 agents x ~4-8 rounds average + summary).
Estimated cost per run: $0.30-0.80.
