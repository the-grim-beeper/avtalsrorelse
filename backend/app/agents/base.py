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
