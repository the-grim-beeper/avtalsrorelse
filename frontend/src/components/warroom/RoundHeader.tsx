interface Props {
  round: number;
  phase: number;
  phaseName: string;
  status: "idle" | "running" | "complete";
}

const PHASE_COUNT = 5;

export function RoundHeader({ round, phase, phaseName, status }: Props) {
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            {status === "complete" ? "Förhandling avslutad" : phaseName || "Väntar..."}
          </h2>
          {status === "running" && (
            <p className="text-sm text-gray-500">Omgång {round}</p>
          )}
        </div>
        {status === "running" && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-swedish-blue rounded-full animate-pulse" />
            <span className="text-xs text-gray-500">Pågår</span>
          </div>
        )}
      </div>

      <div className="flex gap-1">
        {Array.from({ length: PHASE_COUNT }, (_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              i + 1 < phase
                ? "bg-swedish-blue"
                : i + 1 === phase
                  ? "bg-swedish-blue/60"
                  : "bg-gray-200"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
