import type { AgentAction, AgentIdentity, ConflictEvent } from "../../types";
import { ActionFeed } from "./ActionFeed";
import { RoundHeader } from "./RoundHeader";

interface Props {
  round: number;
  phase: number;
  phaseName: string;
  status: "idle" | "running" | "complete";
  actions: AgentAction[];
  conflictEvents: ConflictEvent[];
  agents: Record<string, AgentIdentity>;
  finalSummary: string | null;
}

export function CenterStage({
  round,
  phase,
  phaseName,
  status,
  actions,
  conflictEvents,
  agents,
  finalSummary,
}: Props) {
  return (
    <div className="h-full flex flex-col">
      <RoundHeader round={round} phase={phase} phaseName={phaseName} status={status} />

      {finalSummary ? (
        <div className="flex-1 overflow-y-auto">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Sammanfattning</h3>
            <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {finalSummary}
            </div>
          </div>
        </div>
      ) : (
        <ActionFeed actions={actions} conflictEvents={conflictEvents} agents={agents} />
      )}
    </div>
  );
}
