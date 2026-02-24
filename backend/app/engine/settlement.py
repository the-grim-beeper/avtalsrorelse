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
    union_will = sum(agent_states[uid].willingness_to_settle for uid in pair.union_ids) / len(pair.union_ids)
    emp_will = agent_states[pair.employer_id].willingness_to_settle
    total_will = union_will + emp_will
    if total_will == 0:
        return (avg_union + employer_position) / 2
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
