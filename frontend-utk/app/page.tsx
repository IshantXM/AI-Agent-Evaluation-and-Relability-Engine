"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Cpu, ChevronDown, ChevronUp, Clock, Terminal } from "lucide-react";
import EvaluationPanel, { EvaluationRecord } from "./EvaluationPanel";

interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  status: string;
  latency_ms?: number;
  payload?: any;
}

interface Trace {
  id: number;
  run_id: string;
  agent_id: string;
  agent_version: string;
  task: { input: any; expected_output?: any };
  final_output: string;
  events: TraceEvent[];
  status: string;
}

const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws/traces";

export default function Dashboard() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [evaluations, setEvaluations] = useState<Record<string, EvaluationRecord>>({});
  const [loading, setLoading] = useState(true);
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // 1. Fetch historical traces
    fetch(`${API_BASE}/api/traces`)
      .then((res) => res.json())
      .then((data) => setTraces(data))
      .catch((err) => console.error("Error fetching traces:", err));

    // 2. Fetch historical evaluations, keyed by run_id for quick lookup
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

    // 3. Real-time updates. Every message is now { event_type, data }.
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.event_type === "TRACE_INGESTED") {
        setTraces((prev) => [message.data, ...prev]);
      }

      if (message.event_type === "REPORT_READY") {
        const record: EvaluationRecord = message.data;
        setEvaluations((prev) => ({ ...prev, [record.run_id]: record }));
      }
    };

    return () => ws.close();
  }, []);

  const toggleTrace = (run_id: string) => {
    setExpandedTrace(expandedTrace === run_id ? null : run_id);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header Section */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <Activity className="text-blue-500 w-8 h-8" />
              Aegis Platform Dashboard
            </h1>
            <p className="text-slate-400 mt-1">AI Agent Evaluation & Reliability Engine</p>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg text-sm">
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-emerald-500 animate-pulse" : "bg-slate-600"
              }`}
            />
            <span>{connected ? "Backend Connected" : "Connecting..."}</span>
          </div>
        </div>

        {/* Traces Feed */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-400" />
            Ingested Agent Traces
          </h2>

          {loading ? (
            <p className="text-slate-500">Loading traces from database...</p>
          ) : traces.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
              <p>No traces found yet. Run your Python mock agent!</p>
            </div>
          ) : (
            traces.map((trace) => {
              const evaluation = evaluations[trace.run_id];

              return (
                <div
                  key={trace.id}
                  className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all"
                >
                  {/* Clickable Card Header */}
                  <div
                    className="p-6 cursor-pointer flex flex-col space-y-4"
                    onClick={() => toggleTrace(trace.run_id)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-mono bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-md border border-blue-500/20">
                          {trace.run_id}
                        </span>
                        <h3 className="text-lg font-semibold text-white mt-2 flex items-center gap-2">
                          {trace.agent_id}
                          <span className="text-sm text-slate-500 font-normal">
                            v{trace.agent_version}
                          </span>
                        </h3>
                      </div>
                      <div className="text-right text-sm text-slate-400 flex flex-col items-end gap-2">
                        <span className="flex items-center gap-1">
                          <Cpu className="w-4 h-4 text-indigo-400" />
                          {trace.events?.length || 0} Events
                        </span>
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                            trace.status === "success"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-red-500/10 text-red-400"
                          }`}
                        >
                          {trace.status.toUpperCase()}
                        </span>
                        {evaluation && (
                          <span className="text-xs font-mono text-slate-500">
                            {evaluation.reliability_status ?? "PENDING"}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800/60 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500 block text-xs uppercase font-mono mb-1">
                          Task Input
                        </span>
                        <p className="text-slate-300 truncate">
                          {JSON.stringify(trace.task?.input)}
                        </p>
                      </div>
                      <div className="flex justify-between items-end">
                        <div className="flex-1 overflow-hidden pr-4">
                          <span className="text-slate-500 block text-xs uppercase font-mono mb-1">
                            Final Output
                          </span>
                          <p className="text-emerald-400 truncate">
                            {trace.final_output || "N/A"}
                          </p>
                        </div>
                        {expandedTrace === trace.run_id ? (
                          <ChevronUp className="text-slate-500" />
                        ) : (
                          <ChevronDown className="text-slate-500" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded view: evaluation panel + timeline */}
                  {expandedTrace === trace.run_id && (
                    <div className="px-6 pb-6 pt-2 bg-slate-950/50 border-t border-slate-800">
                      {evaluation ? (
                        <EvaluationPanel evaluation={evaluation} />
                      ) : (
                        <p className="text-xs text-slate-500 mt-4">
                          Evaluation still running or not available for this trace.
                        </p>
                      )}

                      <h4 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2 mt-6">
                        <Terminal className="w-4 h-4" /> Execution Timeline
                      </h4>

                      <div className="relative pl-4 border-l-2 border-slate-800 space-y-6 ml-2">
                        {trace.events?.map((evt) => (
                          <div key={evt.event_id} className="relative">
                            <div
                              className={`absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-slate-950 ${
                                evt.status === "success" ? "bg-blue-500" : "bg-red-500"
                              }`}
                            />
                            <div className="bg-slate-900 border border-slate-800/60 rounded-lg p-4 shadow-sm">
                              <div className="flex justify-between items-start mb-2">
                                <span className="font-mono text-sm text-blue-400 font-semibold">
                                  {evt.event_type}
                                </span>
                                <span className="text-xs text-slate-400 flex items-center gap-1 font-mono bg-slate-950 px-2 py-1 rounded border border-slate-800">
                                  <Clock className="w-3 h-3 text-slate-500" /> {evt.latency_ms}ms
                                </span>
                              </div>
                              {evt.payload && Object.keys(evt.payload).length > 0 && (
                                <pre className="text-xs text-slate-400 bg-slate-950 p-3 rounded mt-3 overflow-x-auto border border-slate-800/40 font-mono">
                                  {JSON.stringify(evt.payload, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </main>
  );
}
