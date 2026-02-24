import { useCallback, useState } from "react";
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
                const newAgentStates = { ...prev.agentStates };
                for (const uid of s.union_ids) {
                  if (newAgentStates[uid]) {
                    newAgentStates[uid] = {
                      ...newAgentStates[uid],
                      is_settled: true,
                      settlement_level: s.level,
                    };
                  }
                }
                if (newAgentStates[s.employer_id]) {
                  newAgentStates[s.employer_id] = {
                    ...newAgentStates[s.employer_id],
                    is_settled: true,
                    settlement_level: s.level,
                  };
                }
                return {
                  ...prev,
                  settlements: [...prev.settlements, s],
                  agentStates: newAgentStates,
                };
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
