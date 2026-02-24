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
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="text-sm text-gray-500 hover:text-gray-800 transition-colors cursor-pointer"
          >
            \u2190 Tillbaka
          </button>
          <h1 className="text-lg font-bold text-gray-900">Avtalsr\u00f6relsen</h1>
        </div>
        {simulation.status === "running" && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-swedish-blue rounded-full animate-pulse" />
            <span className="text-sm text-gray-500">Simulering p\u00e5g\u00e5r...</span>
          </div>
        )}
      </header>

      <div className="flex-1 grid grid-cols-[280px_1fr_260px] gap-4 p-4 min-h-0">
        <div className="min-h-0 overflow-hidden">
          <AgentPanel agents={agents} agentStates={simulation.agentStates} />
        </div>

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

        <div className="min-h-0 overflow-hidden">
          <InfoPanel
            parameters={parameters}
            marke={simulation.marke}
            settlements={simulation.settlements}
          />
        </div>
      </div>
    </div>
  );
}
