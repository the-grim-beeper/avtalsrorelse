import type { ScenarioPreset } from "../../types";

const PRESET_ICONS: Record<string, string> = {
  stabil_tillvaxt: "⚖️",
  inflationschock: "📈",
  "90talskrisen": "📉",
  hogkonjunktur: "🚀",
  gron_omstallning: "🌿",
  pandemi_aterhamtning: "🏥",
};

interface Props {
  preset: ScenarioPreset;
  selected: boolean;
  onSelect: () => void;
}

export function PresetCard({ preset, selected, onSelect }: Props) {
  return (
    <button
      onClick={onSelect}
      className={`text-left p-5 rounded-xl border-2 transition-all duration-200 cursor-pointer
        ${selected
          ? "border-swedish-blue bg-swedish-blue-light shadow-md"
          : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
        }`}
    >
      <div className="text-2xl mb-2">{PRESET_ICONS[preset.id] || "📊"}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{preset.name}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{preset.description}</p>
    </button>
  );
}
