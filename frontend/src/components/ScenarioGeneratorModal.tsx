"use client";

import React, { useState } from "react";
import { Sparkles, X, ShieldAlert, AlertTriangle, Layers, Copy, Check } from "lucide-react";
import { ScenarioItem } from "../types";
import { api } from "../services/api";

interface ScenarioGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ScenarioGeneratorModal: React.FC<ScenarioGeneratorModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [domain, setDomain] = useState("Finance & High-Frequency Trading");
  const [toolsInput, setToolsInput] = useState("execute_order, query_account_balance, cancel_transaction");
  const [loading, setLoading] = useState(false);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const toolList = toolsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      const res = await api.generateScenarios({
        domain,
        tools: toolList,
        num_scenarios: 4,
      });
      setScenarios(res.scenarios);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (scenario: ScenarioItem) => {
    const jsonStr = JSON.stringify(
      {
        task: { input: scenario.prompt },
        agent_id: "probed_agent",
        agent_version: "v1.0.0",
        events: [],
        metrics: {},
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonStr);
    setCopiedId(scenario.scenario_id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "HIGH":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h2 className="text-base font-semibold text-white">
              Adversarial Scenario & Test Case Generator
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Target Domain
              </label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="e.g. Healthcare Diagnostics, Code Execution"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Agent Tools (comma-separated)
              </label>
              <input
                type="text"
                value={toolsInput}
                onChange={(e) => setToolsInput(e.target.value)}
                placeholder="e.g. run_sql, send_email, write_file"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {loading ? "Synthesizing Scenarios..." : "Generate Test Probes"}
            </button>
          </div>

          {/* Results List */}
          {scenarios.length > 0 && (
            <div className="space-y-3 pt-3 border-t border-slate-800">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Generated Evaluation Scenarios ({scenarios.length})
              </h3>
              <div className="space-y-3">
                {scenarios.map((scen) => (
                  <div
                    key={scen.scenario_id}
                    className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-white">{scen.title}</span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getSeverityBadge(
                            scen.severity
                          )}`}
                        >
                          {scen.severity}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          Target: {scen.target_evaluator}
                        </span>
                      </div>
                      <button
                        onClick={() => handleCopy(scen)}
                        className="text-xs flex items-center gap-1 text-slate-400 hover:text-indigo-400 px-2 py-1 rounded bg-slate-900 border border-slate-800"
                        title="Copy as trace payload"
                      >
                        {copiedId === scen.scenario_id ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" />
                            <span className="text-[11px] text-emerald-400">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span className="text-[11px]">Copy JSON</span>
                          </>
                        )}
                      </button>
                    </div>

                    <p className="text-xs text-slate-300 bg-slate-900 p-2 rounded border border-slate-800/60 font-mono">
                      {scen.prompt}
                    </p>

                    <p className="text-[11px] text-slate-500">
                      <strong className="text-slate-400">Expected Behavior:</strong> {scen.expected_behavior}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
