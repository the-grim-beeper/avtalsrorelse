export type AgentType = "union" | "employer" | "confederation" | "mediator";
export type AgentTier = 1 | 2 | 3 | 4;
export type ExportPressure = "low" | "medium" | "high";
export type Relationship = "allied" | "opposed" | "neutral";

export interface MacroParameters {
  inflation: number;
  unemployment: number;
  gdp_growth: number;
  policy_rate: number;
  political_climate: number;
  export_pressure: ExportPressure;
  previous_agreement: number;
}

export interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  flavor_text: string;
  parameters: MacroParameters;
}

export interface AgentIdentity {
  id: string;
  name: string;
  short_name: string;
  agent_type: AgentType;
  tier: AgentTier;
  role_description: string;
  priorities: string[];
  constraints: string[];
  relationships: Record<string, Relationship>;
}

export interface AgentAction {
  agent_id: string;
  round_number: number;
  phase: number;
  position: number;
  reasoning: string;
  public_statement: string;
  willingness_to_settle: number;
}

export interface Settlement {
  union_ids: string[];
  employer_id: string;
  level: number;
  round: number;
}

export interface ConflictEvent {
  event_type: string;
  agent_id: string;
  round_number: number;
  description: string;
}

export interface RoundStart {
  round_number: number;
  phase: number;
  phase_name: string;
  active_agents: string[];
}

export interface RoundEnd {
  round_number: number;
  summary: string;
}

export interface SimulationEnd {
  summary: string;
  outcomes: Settlement[];
  marke: number | null;
}

export interface Mediation {
  description: string;
  union_ids: string[];
  employer_id: string;
  level: number;
}

export interface AgentState {
  agent_id: string;
  current_position: number | null;
  willingness_to_settle: number;
  is_settled: boolean;
  settlement_level: number | null;
  actions: AgentAction[];
}

export type SimulationStatus = "idle" | "running" | "complete";
