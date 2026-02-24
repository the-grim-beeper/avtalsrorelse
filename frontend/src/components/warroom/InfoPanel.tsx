import type { MacroParameters, Settlement } from "../../types";
import { MacroSummary } from "./MacroSummary";
import { SettlementTracker } from "./SettlementTracker";

interface Props {
  parameters: MacroParameters;
  marke: number | null;
  settlements: Settlement[];
}

export function InfoPanel({ parameters, marke, settlements }: Props) {
  return (
    <div className="h-full overflow-y-auto space-y-6 pl-1">
      <MacroSummary parameters={parameters} marke={marke} />
      <SettlementTracker settlements={settlements} />
    </div>
  );
}
