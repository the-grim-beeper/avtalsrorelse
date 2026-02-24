import { useEffect, useState } from "react";
import { fetchAgents, fetchPresets } from "../api/client";
import { AgentRoster } from "../components/setup/AgentRoster";
import { ParameterSliders } from "../components/setup/ParameterSliders";
import { PresetCard } from "../components/setup/PresetCard";
import type { AgentIdentity, MacroParameters, ScenarioPreset } from "../types";

interface Props {
  onStart: (presetId: string | null, parameters: MacroParameters) => void;
}

export function SetupPage({ onStart }: Props) {
  const [presets, setPresets] = useState<ScenarioPreset[]>([]);
  const [agents, setAgents] = useState<AgentIdentity[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [parameters, setParameters] = useState<MacroParameters>({
    inflation: 2.0,
    unemployment: 7.0,
    gdp_growth: 2.0,
    policy_rate: 2.5,
    political_climate: 3,
    export_pressure: "medium",
    previous_agreement: 2.5,
  });

  useEffect(() => {
    fetchPresets().then(setPresets);
    fetchAgents().then(setAgents);
  }, []);

  const handlePresetSelect = (preset: ScenarioPreset) => {
    setSelectedPreset(preset.id);
    setParameters(preset.parameters);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Avtalsrörelsen</h1>
          <p className="text-gray-600 mt-1">Simulering av svensk lönebildning</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Välj scenario</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {presets.map((preset) => (
              <PresetCard
                key={preset.id}
                preset={preset}
                selected={selectedPreset === preset.id}
                onSelect={() => handlePresetSelect(preset)}
              />
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <ParameterSliders parameters={parameters} onChange={setParameters} />
          </section>

          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <AgentRoster agents={agents} />
          </section>
        </div>

        <div className="flex justify-center pt-4">
          <button
            onClick={() => onStart(selectedPreset, parameters)}
            className="px-8 py-3 bg-swedish-blue text-white rounded-xl font-semibold text-lg
                     hover:bg-swedish-blue/90 transition-colors shadow-sm hover:shadow-md
                     active:scale-[0.98] cursor-pointer"
          >
            Starta förhandling
          </button>
        </div>
      </main>
    </div>
  );
}
