import { useEffect, useState } from "react";
import { fetchAgents } from "./api/client";
import { useSimulation } from "./hooks/useSimulation";
import { SetupPage } from "./pages/SetupPage";
import { SimulationPage } from "./pages/SimulationPage";
import type { AgentIdentity, MacroParameters } from "./types";

type View = "setup" | "simulation";

export default function App() {
  const [view, setView] = useState<View>("setup");
  const [agents, setAgents] = useState<AgentIdentity[]>([]);
  const [activeParams, setActiveParams] = useState<MacroParameters | null>(null);
  const { state: simulation, start, reset } = useSimulation();

  useEffect(() => {
    fetchAgents().then(setAgents);
  }, []);

  const handleStart = async (presetId: string | null, parameters: MacroParameters) => {
    setActiveParams(parameters);
    setView("simulation");
    await start(presetId, parameters);
  };

  const handleBack = () => {
    reset();
    setView("setup");
  };

  if (view === "simulation" && activeParams) {
    return (
      <SimulationPage
        agents={agents}
        parameters={activeParams}
        simulation={simulation}
        onBack={handleBack}
      />
    );
  }

  return <SetupPage onStart={handleStart} />;
}
