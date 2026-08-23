"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import {
  Activity,
  Cpu,
  ChevronDown,
  ChevronUp,
  Clock,
  Terminal,
  Upload,
  FileCode,
  Sparkles,
  Download,
  CheckCircle2,
  Layers,
} from "lucide-react";
import EvaluationPanel, { EvaluationRecord } from "./EvaluationPanel";
import { jsPDF } from "jspdf";

interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  status: string;
  latency_ms?: number;
  payload?: Record<string, unknown>;
}

interface Trace {
  id: number;
  run_id: string;
  agent_id: string;
  agent_version: string;
  task: { input: unknown; expected_output?: unknown };
  final_output: string;
  events: TraceEvent[];
  metrics?: {
    latency_ms?: number;
    input_tokens?: number;
    output_tokens?: number;
    llm_calls?: number;
    tool_calls?: number;
    estimated_cost?: number;
  };
  status: string;
}

interface GeneratedScenario {
  scenario_id: string;
  category: string;
  title: string;
  prompt: string;
  target_evaluator: string;
  severity: string;
  expected_behavior: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const WS_URL = `${API_BASE.replace(/^http/, "ws")}/ws/traces`;

function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "N/A" : `${Math.round(value * 100)}%`;
}

export default function Dashboard() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [evaluations, setEvaluations] = useState<Record<string, EvaluationRecord>>({});
  const [loading, setLoading] = useState(true);
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Scenario Generation State
  const [activeTab, setActiveTab] = useState<"traces" | "scenarios">("traces");
  const [agentDomain, setAgentDomain] = useState("Autonomous SQL & Data Agent");
  const [agentTools, setAgentTools] = useState("db_query, schema_inspector, bash_runner");
  const [generatingScenarios, setGeneratingScenarios] = useState(false);
  const [scenarios, setScenarios] = useState<GeneratedScenario[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchHistoricalData = useCallback(() => {
    fetch(`${API_BASE}/api/traces`)
      .then((res) => res.json())
      .then((data) => {
        setTraces(data);
        if (data.length > 0 && !expandedTrace) {
          setExpandedTrace(data[0].run_id);
        }
      })
      .catch((err) => console.error("Error fetching traces:", err));

    fetch(`${API_BASE}/api/evaluations`)
      .then((res) => res.json())
      .then((data: EvaluationRecord[]) => {
        const byRunId: Record<string, EvaluationRecord> = {};
        for (const e of data) byRunId[e.run_id] = e;
        setEvaluations(byRunId);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching evaluations:", err);
        setLoading(false);
      });
  }, [expandedTrace]);

  useEffect(() => {
    fetchHistoricalData();

    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.event_type === "TRACE_INGESTED") {
        setTraces((prev) => [message.data, ...prev]);
        setExpandedTrace(message.data.run_id);
      }

      if (message.event_type === "REPORT_READY") {
        const record: EvaluationRecord = message.data;
        setEvaluations((prev) => ({ ...prev, [record.run_id]: record }));
      }
    };

    return () => ws.close();
  }, [fetchHistoricalData]);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus(`Uploading & evaluating ${file.name}...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/traces/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`Successfully evaluated ${data.traces_evaluated_count || 1} trace(s) from ${file.name}!`);
        fetchHistoricalData();
      } else {
        setUploadStatus(`Upload failed: ${data.detail || "Invalid format"}`);
      }
    } catch (err: unknown) {
      setUploadStatus(`Upload error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleGenerateScenarios = async () => {
    setGeneratingScenarios(true);
    try {
      const toolsList = agentTools.split(",").map((t) => t.trim()).filter(Boolean);
      const res = await fetch(`${API_BASE}/api/scenarios/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: agentDomain, tools: toolsList }),
      });
      const data = await res.json();
      if (res.ok) {
        setScenarios(data.scenarios);
      }
    } catch (err) {
      console.error("Scenario generation failed:", err);
    } finally {
      setGeneratingScenarios(false);
    }
  };

  const downloadReport = (evaluation: EvaluationRecord) => {
    const pdf = new jsPDF();
    const report = evaluation.report;
    let y = 20;

    pdf.setFontSize(18);
    pdf.text("Aegis Reliability Report", 20, y);
    y += 12;
    pdf.setFontSize(10);
    pdf.text(`Run: ${evaluation.run_id}`, 20, y);
    y += 6;
    pdf.text(`Agent: ${evaluation.agent_id} (${evaluation.agent_version})`, 20, y);
    y += 10;
    pdf.setFontSize(13);
    pdf.text(`Overall score: ${formatPercent(evaluation.overall_score)}`, 20, y);
    y += 7;
    pdf.setFontSize(10);
    pdf.text(`Reliability: ${evaluation.reliability_status ?? "PENDING"}`, 20, y);
    y += 12;
    pdf.setFontSize(12);
    pdf.text("Evaluator results", 20, y);
    y += 8;
    pdf.setFontSize(10);
    for (const result of evaluation.evaluations) {
      pdf.text(`${result.evaluator}: ${result.verdict} | score ${formatPercent(result.score)} | confidence ${formatPercent(result.confidence)}`, 24, y);
      y += 6;
      if (y > 275) {
        pdf.addPage();
        y = 20;
      }
    }
    if (report?.failures?.length) {
      y += 6;
      pdf.setFontSize(12);
      pdf.text("Failures", 20, y);
      y += 8;
      pdf.setFontSize(10);
      for (const failure of report.failures) {
        const lines = pdf.splitTextToSize(`- ${failure.description}`, 165);
        pdf.text(lines, 24, y);
        y += lines.length * 5 + 2;
        if (y > 275) {
          pdf.addPage();
          y = 20;
        }
      }
    }
    pdf.save(`Aegis_Reliability_Report_${evaluation.run_id}.pdf`);
  };

  const toggleTrace = (run_id: string) => {
    setExpandedTrace(expandedTrace === run_id ? null : run_id);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-xl">
                <Activity className="text-blue-400 w-7 h-7" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                  Aegis Evaluation Engine
                </h1>
                <p className="text-xs md:text-sm text-slate-400">
                  Continuous Integration & Reliability Assessment for Autonomous AI Agents
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-lg text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  connected ? "bg-emerald-500 animate-pulse" : "bg-slate-600"
                }`}
              />
              <span className="text-slate-400">WebSocket:</span>
              <span className="font-mono text-slate-200">
                {connected ? "LIVE" : "DISCONNECTED"}
              </span>
            </div>
            <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
              <button
                onClick={() => setActiveTab("traces")}
                className={`px-3 py-1 rounded-md transition font-medium ${
                  activeTab === "traces"
                    ? "bg-blue-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Traces & Evals
              </button>
              <button
                onClick={() => setActiveTab("scenarios")}
                className={`px-3 py-1 rounded-md transition font-medium flex items-center gap-1.5 ${
                  activeTab === "scenarios"
                    ? "bg-blue-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Scenario Generator
              </button>
            </div>
          </div>
        </div>

        {activeTab === "traces" ? (
          <>
            {/* File Upload / Drag & Drop Dropzone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  handleFileUpload(e.dataTransfer.files[0]);
                }
              }}
              className="border-2 border-dashed border-slate-800 hover:border-blue-500/50 bg-slate-900/40 hover:bg-slate-900/60 rounded-xl p-6 transition flex flex-col md:flex-row items-center justify-between gap-4"
            >
              <div className="flex items-center gap-4">
                <div className="p-3 bg-slate-800 rounded-lg text-blue-400">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    Drop Agent Trace or Benchmark File (.json / .jsonl)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Directly evaluate pre-recorded execution traces or batch test suites against the active evaluators.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".json,.jsonl"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
                >
                  <FileCode className="w-4 h-4" />
                  {uploading ? "Evaluating..." : "Choose Trace File"}
                </button>
              </div>
            </div>

            {uploadStatus && (
              <div className="p-3 bg-blue-950/40 border border-blue-800/60 rounded-lg text-xs text-blue-300 flex items-center gap-2 animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-blue-400" />
                <span>{uploadStatus}</span>
              </div>
            )}

            {/* Traces List Section */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-blue-400" />
                  Live Execution Traces & Reliability Reports
                </h2>
                <span className="text-xs font-mono text-slate-400">
                  {traces.length} total run(s) recorded
                </span>
              </div>

              {loading ? (
                <div className="text-center py-12 text-slate-500">Loading traces & reports...</div>
              ) : traces.length === 0 ? (
                <div className="text-center py-12 border border-slate-900 rounded-lg text-slate-500 bg-slate-900/20">
                  No traces recorded yet. Run <code>python run_mock_agent.py</code> or upload a trace file.
                </div>
              ) : (
                traces.map((trace) => {
                  const evaluation = evaluations[trace.run_id];
                  const isExpanded = expandedTrace === trace.run_id;

                  return (
                    <div
                      key={trace.run_id}
                      className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm hover:border-slate-700 transition"
                    >
                      {/* Summary Row */}
                      <div
                        onClick={() => toggleTrace(trace.run_id)}
                        className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none bg-slate-900 hover:bg-slate-800/40 transition"
                      >
                        <div className="flex items-start md:items-center gap-3">
                          <div className="p-2 bg-slate-800 rounded-lg text-slate-400">
                            <Cpu className="w-5 h-5 text-blue-400" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-white">
                                {trace.agent_id}
                              </span>
                              <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-400 font-mono">
                                {trace.agent_version}
                              </span>
                              <span className="text-xs font-mono text-slate-500">
                                {trace.run_id}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                              <span className="text-slate-500 font-medium">Task:</span>{" "}
                              {String(trace.task?.input ?? "")}
                            </p>
                          </div>
                        </div>

                        {/* Metrics Pills */}
                        <div className="flex items-center gap-3 flex-wrap">
                          {trace.metrics?.latency_ms && (
                            <div className="flex items-center gap-1.5 text-xs bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-slate-300 font-mono">
                              <Clock className="w-3.5 h-3.5 text-slate-400" />
                              {Math.round(trace.metrics.latency_ms)}ms
                            </div>
                          )}
                          {trace.metrics?.estimated_cost !== undefined && (
                            <div className="text-xs bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-slate-300 font-mono">
                              ${trace.metrics.estimated_cost.toFixed(4)}
                            </div>
                          )}

                          {evaluation ? (
                            <div
                              className={`text-xs px-2.5 py-1 rounded font-bold font-mono border ${
                                evaluation.reliability_status === "RELIABLE"
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                  : evaluation.reliability_status === "DEGRADED"
                                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                  : "bg-red-500/10 text-red-400 border-red-500/30"
                              }`}
                            >
                              {evaluation.overall_score !== null
                                ? `${Math.round(evaluation.overall_score * 100)}%`
                                : "—"}{" "}
                              {evaluation.reliability_status}
                            </div>
                          ) : (
                            <div className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded font-mono">
                              Evaluating...
                            </div>
                          )}

                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      </div>

                      {/* Expanded View */}
                      {isExpanded && (
                        <div className="border-t border-slate-800 p-5 bg-slate-950/60 space-y-6">
                          {/* Top Action Bar */}
                          <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                              Reliability & Multi-Dimension Scorecard
                            </h4>
                            {evaluation && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  downloadReport(evaluation);
                                }}
                                className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition font-medium"
                              >
                                <Download className="w-3.5 h-3.5" />
                                Export Report (PDF)
                              </button>
                            )}
                          </div>

                          {/* Evaluation Panel */}
                          {evaluation ? (
                            <EvaluationPanel evaluation={evaluation} />
                          ) : (
                            <div className="text-xs text-slate-500 italic p-3 bg-slate-950 rounded">
                              Evaluation in progress for this run...
                            </div>
                          )}

                          {/* Execution Timeline */}
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                              Agent Execution Timeline ({trace.events?.length || 0} events)
                            </h4>
                            <div className="space-y-2">
                              {trace.events?.map((ev, idx) => (
                                <div
                                  key={ev.event_id || idx}
                                  className="flex items-start gap-3 p-3 rounded-lg bg-slate-900 border border-slate-800/80 text-xs"
                                >
                                  <span className="font-mono text-slate-500 mt-0.5">
                                    {String(idx + 1).padStart(2, "0")}
                                  </span>
                                  <div className="flex-1">
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono font-bold text-blue-400 uppercase">
                                          {ev.event_type}
                                        </span>
                                        <span
                                          className={`px-1.5 py-0.2 rounded text-[10px] font-mono ${
                                            ev.status === "success"
                                              ? "text-emerald-400 bg-emerald-950/60"
                                              : "text-red-400 bg-red-950/60"
                                          }`}
                                        >
                                          {ev.status}
                                        </span>
                                      </div>
                                      <span className="text-slate-500 font-mono">
                                        {ev.latency_ms ? `${Math.round(ev.latency_ms)}ms` : "—"}
                                      </span>
                                    </div>
                                    {ev.payload && Object.keys(ev.payload).length > 0 && (
                                      <pre className="mt-2 p-2 bg-slate-950 rounded text-slate-300 font-mono text-[11px] overflow-x-auto">
                                        {JSON.stringify(ev.payload, null, 2)}
                                      </pre>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Final Output */}
                          {trace.final_output && (
                            <div>
                              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                                Final Agent Output
                              </h4>
                              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-200">
                                {trace.final_output}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </>
        ) : (
          /* Scenario Generation Engine Playground (Pillar 1 & 4) */
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-purple-600/20 border border-purple-500/30 rounded-lg text-purple-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">
                    Scenario Generation Engine (Pillar 1 & 4)
                  </h2>
                  <p className="text-xs text-slate-400">
                    Automatically synthesizes realistic multi-step tasks, adversarial prompt injections, destructive action probes, and tool-loop triggers.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Agent Domain / Role
                  </label>
                  <input
                    type="text"
                    value={agentDomain}
                    onChange={(e) => setAgentDomain(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Healthcare Clinical Assistant, DevOps Deployer"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Available Tools (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={agentTools}
                    onChange={(e) => setAgentTools(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
                    placeholder="e.g. sql_query, bash_exec, http_get"
                  />
                </div>
              </div>

              <button
                onClick={handleGenerateScenarios}
                disabled={generatingScenarios}
                className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-lg text-xs font-bold flex items-center gap-2 transition disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {generatingScenarios ? "Generating Test Scenarios..." : "Generate Test Scenarios"}
              </button>
            </div>

            {scenarios.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  Generated Test Cases ({scenarios.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {scenarios.map((scen) => (
                    <div
                      key={scen.scenario_id}
                      className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                            scen.severity === "CRITICAL"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30"
                              : scen.severity === "HIGH"
                              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                          }`}
                        >
                          {scen.category}
                        </span>
                        <span className="text-xs text-slate-500 font-mono">
                          Target: {scen.target_evaluator}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-white">{scen.title}</h4>
                      <p className="text-xs text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800 font-mono">
                        {scen.prompt}
                      </p>
                      <div className="text-[11px] text-slate-400">
                        <span className="text-slate-500 font-semibold">Expected Behavior:</span>{" "}
                        {scen.expected_behavior}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
