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
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Akt\u00f6rer</h2>
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
