import { useState } from "react";
import type { AgentIdentity, AgentState } from "../../types";

interface Props {
  identity: AgentIdentity;
  state: AgentState | undefined;
}

const TYPE_BADGE: Record<string, { label: string; cls: string }> = {
  union: { label: "Fack", cls: "bg-blue-100 text-blue-700" },
  employer: { label: "AG", cls: "bg-amber-100 text-amber-700" },
  confederation: { label: "CO", cls: "bg-purple-100 text-purple-700" },
  mediator: { label: "MI", cls: "bg-green-100 text-green-700" },
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
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${badge.cls}`}>
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

        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${sentimentColor(willingness)}`}
            style={{ width: `${willingness}%` }}
          />
        </div>
      </div>

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
            <span>F\u00f6rhandlingsvilja: {willingness}/100</span>
            <span>Omg\u00e5ng {lastAction.round_number}</span>
          </div>
        </div>
      )}
    </div>
  );
}
