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
            NegotiationPair(union_ids=["if_metall", "unionen"], employer_id="teknikforetagen", phase=Phase.INDUSTRIAVTALET),
            NegotiationPair(union_ids=["handels"], employer_id="svensk_handel", phase=Phase.PRIVATE_SECTOR),
            NegotiationPair(union_ids=["unionen"], employer_id="almega", phase=Phase.PRIVATE_SECTOR),
            NegotiationPair(union_ids=["kommunal", "vision", "vardforbundet"], employer_id="skr", phase=Phase.PUBLIC_SECTOR),
        ]

    def _get_active_agents(self, phase: Phase) -> list[str]:
        if phase == Phase.OPENING:
            return list(AGENTS.keys())
        tier_map = {
            Phase.INDUSTRIAVTALET: [1],
            Phase.PRIVATE_SECTOR: [2],
            Phase.PUBLIC_SECTOR: [3],
        }
        tiers = tier_map.get(phase, [])
        active = [aid for aid, a in AGENTS.items() if a.tier.value in tiers]
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
        for rnd in self.sim.rounds[-3:]:
            for action in rnd.actions:
                if action.agent_id != agent_id:
                    agent = AGENTS[action.agent_id]
                    lines.append(f"Round {rnd.round_number}: {agent.name} — {action.public_statement}")
        return "\n".join(lines) if lines else "No history yet."

    def _check_phase_complete(self, phase: Phase) -> bool:
        pairs = [p for p in self.sim.negotiation_pairs if p.phase == phase]
        return all(p.is_settled for p in pairs)

    async def run(self) -> AsyncGenerator[dict, None]:
        async for event in self._run_opening():
            yield event
        async for event in self._run_negotiation_phase(Phase.INDUSTRIAVTALET, max_rounds=6, stall_round=4):
            yield event
        async for event in self._run_negotiation_phase(Phase.PRIVATE_SECTOR, max_rounds=4, stall_round=3):
            yield event
        async for event in self._run_negotiation_phase(Phase.PUBLIC_SECTOR, max_rounds=4, stall_round=3):
            yield event
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

            all_positions = self._format_positions(active_agents)
            special_context = ""
            if r >= stall_round:
                special_context = (
                    "NEGOTIATIONS ARE STALLING. Medlingsinstitutet is considering intervention. "
                    "Pressure to settle is mounting from all sides."
                )

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

            negotiating_ids = [
                aid for aid in active_agents
                if AGENTS[aid].agent_type in (AgentType.UNION, AgentType.EMPLOYER)
            ]
            conflict_events = check_conflict_events(
                self.sim.agent_states, round_num, negotiating_ids
            )
            for event in conflict_events:
                yield {"event": "conflict_event", "data": event.model_dump()}

            settlements = []
            for pair in self.sim.negotiation_pairs:
                if pair.phase == phase and not pair.is_settled:
                    if check_settlement(pair, self.sim.agent_states):
                        level = calculate_settlement_level(pair, self.sim.agent_states)
                        pair.is_settled = True
                        pair.settlement_level = round(level, 1)
                        pair.settlement_round = round_num
                        for uid in pair.union_ids:
                            self.sim.agent_states[uid].is_settled = True
                            self.sim.agent_states[uid].settlement_level = pair.settlement_level
                        self.sim.agent_states[pair.employer_id].is_settled = True
                        self.sim.agent_states[pair.employer_id].settlement_level = pair.settlement_level
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

            if self._check_phase_complete(phase):
                break

        # Force settlement for remaining unsettled pairs
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
