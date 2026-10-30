import { Trace, EvaluationRecord, ScenarioGenerationResponse } from "../types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
export const WS_URL = `${API_BASE.replace(/^http/, "ws")}/ws/traces`;

/**
 * Robust API Client with standard error handling and typed responses.
 */
export const api = {
  async getTraces(): Promise<Trace[]> {
    const res = await fetch(`${API_BASE}/api/traces`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch traces: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },

  async getEvaluations(): Promise<EvaluationRecord[]> {
    const res = await fetch(`${API_BASE}/api/evaluations`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch evaluations: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },

  async getEvaluation(runId: string): Promise<EvaluationRecord> {
    const res = await fetch(`${API_BASE}/api/evaluations/${encodeURIComponent(runId)}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch evaluation for ${runId}: ${res.status}`);
    }
    return res.json();
  },

  async uploadTraceFile(file: File): Promise<{
    status: string;
    file_processed: string;
    traces_evaluated_count: number;
    results: any[];
  }> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/api/traces/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Upload failed with status ${res.status}`);
    }

    return res.json();
  },

  async generateScenarios(params: {
    domain: string;
    tools?: string[];
    num_scenarios?: number;
  }): Promise<ScenarioGenerationResponse> {
    const res = await fetch(`${API_BASE}/api/scenarios/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || "Failed to generate scenarios");
    }

    return res.json();
  },
};
