import { useEffect, useRef } from "react";
import type { AgentAction, AgentIdentity, ConflictEvent } from "../../types";

type FeedItem =
  | { type: "action"; data: AgentAction }
  | { type: "conflict"; data: ConflictEvent };

interface Props {
  actions: AgentAction[];
  conflictEvents: ConflictEvent[];
  agents: Record<string, AgentIdentity>;
}

export function ActionFeed({ actions, conflictEvents, agents }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const feed: FeedItem[] = [
    ...actions.map((a) => ({ type: "action" as const, data: a })),
    ...conflictEvents.map((c) => ({ type: "conflict" as const, data: c })),
  ].sort((a, b) => {
    const rA = a.data.round_number;
    const rB = b.data.round_number;
    return rA - rB;
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [feed.length]);

  return (
    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
      {feed.map((item, i) => {
        if (item.type === "conflict") {
          return (
            <div
              key={`conflict-${i}`}
              className="p-3 rounded-lg bg-firm-red/5 border border-firm-red/20"
            >
              <p className="text-sm font-semibold text-firm-red">{item.data.description}</p>
            </div>
          );
        }

        const agent = agents[item.data.agent_id];
        if (!agent) return null;

        return (
          <div
            key={`action-${i}`}
            className="p-3 rounded-lg bg-white border border-gray-100 shadow-sm"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-gray-900">{agent.short_name}</span>
              <span className="text-[10px] text-gray-400">Omg\u00e5ng {item.data.round_number}</span>
            </div>
            <p className="text-sm text-gray-700 italic">"{item.data.public_statement}"</p>
            <div className="flex items-center gap-3 mt-1.5">
              <span className="text-xs font-mono text-gray-600">
                Position: {item.data.position.toFixed(1)}%
              </span>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-600">
                Vilja: {item.data.willingness_to_settle}/100
              </span>
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
