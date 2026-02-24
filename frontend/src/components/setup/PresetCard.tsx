import type { ScenarioPreset } from "../../types";

const PRESET_ICONS: Record<string, string> = {
  stabil_tillvaxt: "\u2696\uFE0F",
  inflationschock: "\uD83D\uDCC8",
  "90talskrisen": "\uD83D\uDCC9",
  hogkonjunktur: "\uD83D\uDE80",
  gron_omstallning: "\uD83C\uDF3F",
  pandemi_aterhamtning: "\uD83C\uDFE5",
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
      <div className="text-2xl mb-2">{PRESET_ICONS[preset.id] || "\uD83D\uDCCA"}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{preset.name}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{preset.description}</p>
    </button>
  );
}
