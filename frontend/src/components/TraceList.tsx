"use client";

import React from "react";
import { Cpu, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { Trace, EvaluationRecord } from "../types";

interface TraceListProps {
  traces: Trace[];
  evaluations: Record<string, EvaluationRecord>;
  selectedRunId: string | null;
  onSelectTrace: (runId: string) => void;
}

export const TraceList: React.FC<TraceListProps> = ({
  traces,
  evaluations,
  selectedRunId,
  onSelectTrace,
}) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between pb-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Ingested Traces ({traces.length})
        </h2>
      </div>

      <div className="space-y-2 max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
        {traces.map((trace) => {
          const isSelected = selectedRunId === trace.run_id;
          const evaluation = evaluations[trace.run_id];
          const score = evaluation?.overall_score;

          return (
            <div
              key={trace.run_id}
              onClick={() => onSelectTrace(trace.run_id)}
              className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                isSelected
                  ? "bg-indigo-600/10 border-indigo-500/50 shadow-md"
                  : "bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-white truncate">
                      {trace.agent_id}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded">
                      {trace.agent_version}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 truncate">
                    {trace.run_id}
                  </div>
                </div>

                {/* Score badge */}
                {score !== undefined && score !== null ? (
                  <div
                    className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${
                      score >= 0.8
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : score >= 0.5
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-red-500/10 text-red-400 border-red-500/20"
                    }`}
                  >
                    {Math.round(score * 100)}%
                  </div>
                ) : (
                  <div className="text-[10px] text-slate-500 font-mono">Pending</div>
                )}
              </div>

              {/* Quick stats footer */}
              <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-3 text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  {trace.metrics?.latency_ms?.toFixed(0) || 0}ms
                </span>
                <span className="flex items-center gap-1">
                  <Cpu className="w-3 h-3 text-slate-500" />
                  {trace.events?.length || 0} events
                </span>
                <span className="ml-auto font-mono text-slate-500">
                  {trace.status.toUpperCase()}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
