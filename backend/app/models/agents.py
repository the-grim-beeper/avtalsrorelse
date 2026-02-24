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
    current_position: float | None = None
    willingness_to_settle: int = Field(50, ge=0, le=100)
    rounds_at_low_willingness: int = 0
    has_threatened_action: bool = False
    is_settled: bool = False
    settlement_level: float | None = None


class AgentAction(BaseModel):
    agent_id: str
    round_number: int
    phase: int
    position: float
    reasoning: str
    public_statement: str
    willingness_to_settle: int = Field(ge=0, le=100)
