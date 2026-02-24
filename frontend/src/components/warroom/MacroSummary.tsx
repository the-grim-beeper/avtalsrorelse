import type { MacroParameters } from "../../types";

interface Props {
  parameters: MacroParameters;
  marke: number | null;
}

export function MacroSummary({ parameters, marke }: Props) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Makro</h3>

      {marke !== null && (
        <div className="p-3 rounded-lg bg-swedish-gold-light border border-swedish-gold/30">
          <p className="text-[10px] uppercase text-gray-500 font-medium">Märket</p>
          <p className="text-2xl font-bold text-gray-900 font-mono">{marke}%</p>
        </div>
      )}

      <div className="space-y-1.5">
        {[
          { label: "Inflation", value: `${parameters.inflation.toFixed(1)}%` },
          { label: "Arbetslöshet", value: `${parameters.unemployment.toFixed(1)}%` },
          { label: "BNP-tillväxt", value: `${parameters.gdp_growth.toFixed(1)}%` },
          { label: "Styrränta", value: `${parameters.policy_rate.toFixed(1)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="flex justify-between text-xs">
            <span className="text-gray-500">{label}</span>
            <span className="font-mono text-gray-800">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
