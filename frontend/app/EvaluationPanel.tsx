"use client";

import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Gauge,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

export interface EvaluationResult {
  evaluation_id: string;
  evaluator: string;
  verdict: "PASS" | "FAIL" | "PARTIAL" | "ERROR";
  score: number;
  confidence: number;
  summary: string;
  findings: { finding_id: string; description: string; severity: string }[];
}

export interface ReliabilityReport {
  report_id: string;
  run_id: string;
  overall_score: number;
  confidence: number;
  regression: {
    status: "IMPROVED" | "REGRESSED" | "UNCHANGED" | "BASELINE" | "NOT_AVAILABLE";
    previous_score: number | null;
    score_delta: number | null;
    previous_version: string | null;
  };
  failures: { failure_id: string; severity: string; description: string }[];
}

export interface EvaluationRecord {
  run_id: string;
  agent_id: string;
  agent_version: string;
  overall_score: number | null;
  reliability_status: "RELIABLE" | "DEGRADED" | "UNRELIABLE" | "INSUFFICIENT_EVIDENCE" | null;
  evaluations: EvaluationResult[];
  report: ReliabilityReport;
}

const VERDICT_STYLES: Record<string, string> = {
  PASS: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  FAIL: "bg-red-500/10 text-red-400 border-red-500/20",
  PARTIAL: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  ERROR: "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

const RELIABILITY_STYLES: Record<string, { color: string; icon: typeof ShieldCheck }> = {
  RELIABLE: { color: "text-emerald-400", icon: ShieldCheck },
  DEGRADED: { color: "text-amber-400", icon: ShieldAlert },
  UNRELIABLE: { color: "text-red-400", icon: ShieldX },
  INSUFFICIENT_EVIDENCE: { color: "text-slate-400", icon: ShieldAlert },
};

function pct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}

function RegressionBadge({ regression }: { regression: ReliabilityReport["regression"] }) {
  if (!regression || regression.status === "NOT_AVAILABLE") return null;

  const config: Record<string, { icon: typeof TrendingUp; color: string; label: string }> = {
    IMPROVED: { icon: TrendingUp, color: "text-emerald-400", label: "Improved" },
    REGRESSED: { icon: TrendingDown, color: "text-red-400", label: "Regressed" },
    UNCHANGED: { icon: Minus, color: "text-slate-400", label: "Unchanged" },
    BASELINE: { icon: Minus, color: "text-slate-400", label: "Baseline run" },
  };
  const c = config[regression.status];
  if (!c) return null;
  const Icon = c.icon;

  return (
    <div className={`flex items-center gap-1.5 text-xs font-medium ${c.color}`}>
      <Icon className="w-3.5 h-3.5" />
      <span>{c.label}</span>
      {regression.score_delta !== null && regression.previous_version && (
        <span className="text-slate-500 font-mono">
          ({regression.score_delta >= 0 ? "+" : ""}
          {Math.round(regression.score_delta * 100)}% vs v{regression.previous_version})
        </span>
      )}
    </div>
  );
}

export default function EvaluationPanel({ evaluation }: { evaluation: EvaluationRecord }) {
  const reliability = evaluation.reliability_status
    ? RELIABILITY_STYLES[evaluation.reliability_status]
    : null;
  const ReliabilityIcon = reliability?.icon ?? Gauge;

  return (
    <div className="mt-4 bg-slate-950 border border-slate-800/60 rounded-lg p-4 space-y-4">
      {/* Header: overall score + reliability status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ReliabilityIcon className={`w-4 h-4 ${reliability?.color ?? "text-slate-400"}`} />
          <span className="text-sm font-semibold text-slate-200">
            {evaluation.reliability_status ?? "PENDING"}
          </span>
          <span className="text-slate-600">·</span>
          <span className="text-sm font-mono text-slate-300">
            {pct(evaluation.overall_score)} overall
          </span>
        </div>
        <RegressionBadge regression={evaluation.report?.regression} />
      </div>

      {/* Per-evaluator verdict grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {evaluation.evaluations.map((ev) => (
          <div
            key={ev.evaluation_id}
            className={`border rounded-md px-3 py-2 ${VERDICT_STYLES[ev.verdict] ?? VERDICT_STYLES.ERROR}`}
            title={ev.summary}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wide opacity-80">
                {ev.evaluator}
              </span>
              <span className="text-xs font-bold">{ev.verdict}</span>
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px] opacity-70">
              <span>score {pct(ev.score)}</span>
              <span>conf {pct(ev.confidence)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Failures, if any */}
      {evaluation.report?.failures?.length > 0 && (
        <div className="pt-2 border-t border-slate-800/60 space-y-1.5">
          <span className="text-xs uppercase font-mono text-slate-500">
            Failures ({evaluation.report.failures.length})
          </span>
          {evaluation.report.failures.map((f) => (
            <div key={f.failure_id} className="text-xs text-slate-400 flex items-start gap-2">
              <span
                className={`mt-0.5 inline-block w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  f.severity === "critical" || f.severity === "high"
                    ? "bg-red-500"
                    : "bg-amber-500"
                }`}
              />
              <span>{f.description}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
