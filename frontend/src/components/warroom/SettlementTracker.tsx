import type { Settlement } from "../../types";

interface NegotiationPairDef {
  label: string;
  union_ids: string[];
  employer_id: string;
}

const PAIRS: NegotiationPairDef[] = [
  { label: "Industriavtalet", union_ids: ["if_metall", "unionen"], employer_id: "teknikforetagen" },
  { label: "Handels \u2013 Sv Handel", union_ids: ["handels"], employer_id: "svensk_handel" },
  { label: "Unionen \u2013 Almega", union_ids: ["unionen"], employer_id: "almega" },
  { label: "Offentlig sektor", union_ids: ["kommunal", "vision", "vardforbundet"], employer_id: "skr" },
];

interface Props {
  settlements: Settlement[];
}

export function SettlementTracker({ settlements }: Props) {
  const isSettled = (pair: NegotiationPairDef): Settlement | undefined => {
    return settlements.find(
      (s) => s.employer_id === pair.employer_id && s.union_ids.some((u) => pair.union_ids.includes(u)),
    );
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Avtal</h3>
      <div className="space-y-2">
        {PAIRS.map((pair) => {
          const settlement = isSettled(pair);
          return (
            <div
              key={pair.label}
              className={`flex items-center justify-between p-2 rounded-lg border transition-colors ${
                settlement
                  ? "border-settle-green/30 bg-settle-green/5"
                  : "border-gray-100 bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full border-2 transition-colors ${
                    settlement ? "bg-settle-green border-settle-green" : "border-gray-300"
                  }`}
                />
                <span className="text-xs text-gray-700">{pair.label}</span>
              </div>
              {settlement && (
                <span className="text-xs font-bold font-mono text-settle-green">
                  {settlement.level}%
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
