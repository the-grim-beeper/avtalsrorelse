import type { AgentIdentity } from "../../types";

const TYPE_COLORS: Record<string, string> = {
  union: "bg-blue-100 text-blue-800",
  employer: "bg-amber-100 text-amber-800",
  confederation: "bg-purple-100 text-purple-800",
  mediator: "bg-green-100 text-green-800",
};

const TYPE_LABELS: Record<string, string> = {
  union: "Fackf\u00f6rbund",
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
      <h3 className="font-semibold text-gray-900">Akt\u00f6rer</h3>
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
