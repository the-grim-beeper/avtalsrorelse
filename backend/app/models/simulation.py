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
    event_type: str
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
    marke: float | None = None
    is_complete: bool = False
    final_summary: str = ""
