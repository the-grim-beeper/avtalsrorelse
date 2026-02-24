import type { ExportPressure, MacroParameters } from "../../types";

interface Props {
  parameters: MacroParameters;
  onChange: (params: MacroParameters) => void;
}

interface SliderConfig {
  key: keyof MacroParameters;
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
}

const SLIDERS: SliderConfig[] = [
  { key: "inflation", label: "Inflation (KPI)", min: 0, max: 15, step: 0.1, unit: "%" },
  { key: "unemployment", label: "Arbetslöshet", min: 2, max: 15, step: 0.1, unit: "%" },
  { key: "gdp_growth", label: "BNP-tillväxt", min: -5, max: 8, step: 0.1, unit: "%" },
  { key: "policy_rate", label: "Styrränta", min: -0.5, max: 10, step: 0.25, unit: "%" },
  { key: "previous_agreement", label: "Tidigare märke", min: 0, max: 8, step: 0.1, unit: "%" },
];

const POLITICAL_LABELS = ["", "Vänster", "Mittvänster", "Mitten", "Mitterhöger", "Höger"];

export function ParameterSliders({ parameters, onChange }: Props) {
  const update = (key: string, value: number | string) => {
    onChange({ ...parameters, [key]: value });
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-900">Makroparametrar</h3>

      {SLIDERS.map((s) => (
        <div key={s.key}>
          <div className="flex justify-between text-sm mb-1">
            <label className="text-gray-700">{s.label}</label>
            <span className="font-mono text-gray-900">
              {(parameters[s.key] as number).toFixed(1)}{s.unit}
            </span>
          </div>
          <input
            type="range"
            min={s.min}
            max={s.max}
            step={s.step}
            value={parameters[s.key] as number}
            onChange={(e) => update(s.key, parseFloat(e.target.value))}
            className="w-full accent-swedish-blue"
          />
        </div>
      ))}

      <div>
        <div className="flex justify-between text-sm mb-1">
          <label className="text-gray-700">Politiskt klimat</label>
          <span className="font-mono text-gray-900">
            {POLITICAL_LABELS[parameters.political_climate]}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={parameters.political_climate}
          onChange={(e) => update("political_climate", parseInt(e.target.value))}
          className="w-full accent-swedish-blue"
        />
      </div>

      <div>
        <label className="text-sm text-gray-700 block mb-1">Exporttryck</label>
        <div className="flex gap-2">
          {(["low", "medium", "high"] as ExportPressure[]).map((level) => (
            <button
              key={level}
              onClick={() => update("export_pressure", level)}
              className={`px-3 py-1 rounded-md text-sm transition-colors cursor-pointer ${
                parameters.export_pressure === level
                  ? "bg-swedish-blue text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {level === "low" ? "Lågt" : level === "medium" ? "Medel" : "Högt"}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
