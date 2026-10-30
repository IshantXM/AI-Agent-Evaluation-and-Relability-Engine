"use client";

import React, { useState } from "react";
import {
  Clock,
  Cpu,
  Terminal,
  Download,
  ChevronDown,
  ChevronUp,
  FileCode,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Trace, EvaluationRecord } from "../types";
import { exportTracePDF } from "../utils/pdfExport";
import EvaluationPanel from "../../app/EvaluationPanel";

interface TraceDetailsProps {
  trace: Trace;
  evaluation?: EvaluationRecord;
}

export const TraceDetails: React.FC<TraceDetailsProps> = ({ trace, evaluation }) => {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const toggleEvent = (eventId: string) => {
    setExpandedEventId((prev) => (prev === eventId ? null : eventId));
  };

  const scorePct =
    evaluation?.overall_score !== null && evaluation?.overall_score !== undefined
      ? `${Math.round(evaluation.overall_score * 100)}%`
      : "Pending";

  return (
    <div className="space-y-6">
      {/* Top Banner & Metadata */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-white">{trace.agent_id}</h2>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700">
                {trace.agent_version}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${
                  trace.status === "success"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                }`}
              >
                {trace.status.toUpperCase()}
              </span>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">Run ID: {trace.run_id}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => exportTracePDF(trace, evaluation)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              Export PDF Report
            </button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/80">
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
            <span className="text-[10px] text-slate-400 font-medium">Reliability Score</span>
            <div className="text-base font-bold text-white font-mono mt-0.5">{scorePct}</div>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
            <span className="text-[10px] text-slate-400 font-medium">Total Latency</span>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {trace.metrics?.latency_ms?.toFixed(0) || 0} ms
            </div>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
            <span className="text-[10px] text-slate-400 font-medium">Token Consumption</span>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {(trace.metrics?.input_tokens || 0) + (trace.metrics?.output_tokens || 0)}
            </div>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
            <span className="text-[10px] text-slate-400 font-medium">Est. Compute Cost</span>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              ${trace.metrics?.estimated_cost?.toFixed(5) || "0.00000"}
            </div>
          </div>
        </div>
      </div>

      {/* Evaluation Results Panel */}
      {evaluation && <EvaluationPanel evaluation={evaluation} />}

      {/* Task Input & Output Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Task Input */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Terminal className="w-4 h-4 text-indigo-400" />
            Task Input Prompt
          </div>
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-48 whitespace-pre-wrap">
            {typeof trace.task?.input === "string"
              ? trace.task.input
              : JSON.stringify(trace.task?.input, null, 2)}
          </div>
        </div>

        {/* Final Output */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <FileCode className="w-4 h-4 text-emerald-400" />
            Agent Final Output
          </div>
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-48 whitespace-pre-wrap">
            {trace.final_output || "No output registered."}
          </div>
        </div>
      </div>

      {/* Execution Trace Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Event Execution Flow ({trace.events?.length || 0})
          </h3>
        </div>

        <div className="space-y-2.5">
          {trace.events?.map((ev, index) => {
            const isExpanded = expandedEventId === ev.event_id;

            return (
              <div
                key={ev.event_id || index}
                className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 transition-colors"
              >
                <div
                  onClick={() => toggleEvent(ev.event_id)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      #{index + 1}
                    </span>
                    <span className="text-xs font-medium text-white">{ev.event_type}</span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        ev.status === "success"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      {ev.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {ev.latency_ms !== undefined && (
                      <span className="text-[11px] font-mono text-slate-500">
                        {ev.latency_ms.toFixed(0)}ms
                      </span>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                </div>

                {/* Event Payload */}
                {isExpanded && ev.payload && (
                  <div className="mt-3 pt-3 border-t border-slate-800 font-mono text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded overflow-x-auto">
                    <pre>{JSON.stringify(ev.payload, null, 2)}</pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
