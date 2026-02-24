import type { AgentIdentity, MacroParameters, ScenarioPreset } from "../types";

const BASE = "/api";

export async function fetchPresets(): Promise<ScenarioPreset[]> {
  const res = await fetch(`${BASE}/presets`);
  return res.json();
}

export async function fetchAgents(): Promise<AgentIdentity[]> {
  const res = await fetch(`${BASE}/agents`);
  return res.json();
}

export interface SSEEvent {
  event: string;
  data: string;
}

export async function* streamSimulation(
  presetId: string | null,
  parameters: MacroParameters | null,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset_id: presetId, parameters }),
  });

  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    let currentData = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        currentData = line.slice(5).trim();
      } else if (line === "" && currentEvent && currentData) {
        yield { event: currentEvent, data: currentData };
        currentEvent = "";
        currentData = "";
      }
    }
  }
}
