export interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  status: string;
  latency_ms?: number;
  payload?: Record<string, unknown>;
}

export interface TraceMetrics {
  latency_ms?: number;
  input_tokens?: number;
  output_tokens?: number;
  llm_calls?: number;
  tool_calls?: number;
  estimated_cost?: number;
}

export interface TraceTask {
  input: unknown;
  expected_output?: unknown;
}

export interface Trace {
  id?: number;
  run_id: string;
  agent_id: string;
  agent_version: string;
  task_id?: string;
  task: TraceTask;
  final_output: string;
  events: TraceEvent[];
  metrics?: TraceMetrics;
  status: string;
  created_at?: string;
}

export interface EvaluationFinding {
  finding_id: string;
  description: string;
  severity: string;
}

export interface EvaluationResult {
  evaluation_id: string;
  evaluator: string;
  verdict: "PASS" | "FAIL" | "PARTIAL" | "ERROR";
  score: number;
  confidence: number;
  summary: string;
  findings: EvaluationFinding[];
}

export interface ReliabilityRegression {
  status: "IMPROVED" | "REGRESSED" | "UNCHANGED" | "BASELINE" | "NOT_AVAILABLE";
  previous_score: number | null;
  score_delta: number | null;
  previous_version: string | null;
}

export interface ReliabilityReport {
  report_id: string;
  run_id: string;
  overall_score: number;
  confidence: number;
  regression: ReliabilityRegression;
  failures: { failure_id: string; severity: string; description: string }[];
}

export interface EvaluationRecord {
  run_id: string;
  agent_id: string;
  agent_version: string;
  overall_score: number | null;
  reliability_status: "RELIABLE" | "DEGRADED" | "UNRELIABLE" | "INSUFFICIENT_EVIDENCE" | null;
  evaluations: EvaluationResult[];
  consensus?: Record<string, unknown>;
  adversarial_summary?: Record<string, unknown>;
  reliability?: Record<string, unknown>;
  report: ReliabilityReport;
  created_at?: string;
}

export interface ScenarioItem {
  scenario_id: string;
  category: string;
  title: string;
  prompt: string;
  target_evaluator: string;
  severity: string;
  expected_behavior: string;
}

export interface ScenarioGenerationResponse {
  status: string;
  domain: string;
  tools_evaluated: string[];
  total_scenarios_generated: number;
  scenarios: ScenarioItem[];
}

export interface WebSocketMessage {
  event_type: "TRACE_INGESTED" | "REPORT_READY" | string;
  data: any;
}
