"use client";

import { useState } from "react";
import { Activity, AlertCircle } from "lucide-react";
import { useTraceStream } from "../src/hooks/useTraceStream";
import { Header, TraceList, TraceDetails, ScenarioGeneratorModal } from "../src/components";

export default function Dashboard() {
  const {
    traces,
    evaluations,
    loading,
    connected,
    error,
    selectedRunId,
    setSelectedRunId,
    refetch,
    uploadTraceFile,
    uploading,
    uploadStatus,
  } = useTraceStream();

  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);

  const selectedTrace = traces.find((t) => t.run_id === selectedRunId) || traces[0];
  const selectedEvaluation = selectedTrace ? evaluations[selectedTrace.run_id] : undefined;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Application Header */}
      <Header
        connected={connected}
        uploading={uploading}
        uploadStatus={uploadStatus}
        onFileUpload={uploadTraceFile}
        onOpenScenarioModal={() => setIsScenarioModalOpen(true)}
        onRefresh={refetch}
      />

      {/* Error alert if backend cannot be reached */}
      {error && (
        <div className="max-w-7xl mx-auto px-6 pt-4 w-full">
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-6 flex-1 w-full">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-500">
            <Activity className="w-8 h-8 animate-spin text-indigo-500" />
            <span className="text-xs font-mono">Connecting to Aegis Engine Stream...</span>
          </div>
        ) : traces.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 border border-dashed border-slate-800 rounded-xl p-8 text-center">
            <Activity className="w-10 h-10 text-slate-600" />
            <h3 className="text-sm font-semibold text-slate-300">No Traces Recorded</h3>
            <p className="text-xs text-slate-500 max-w-sm">
              Ingest an agent execution trace or click &ldquo;Upload Trace&rdquo; above to inspect reliability reports and metrics.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Sidebar Traces List (1 col) */}
            <div className="lg:col-span-1">
              <TraceList
                traces={traces}
                evaluations={evaluations}
                selectedRunId={selectedTrace?.run_id || null}
                onSelectTrace={(runId) => setSelectedRunId(runId)}
              />
            </div>

            {/* Selected Trace Details & Evaluator Breakdown (2 cols) */}
            <div className="lg:col-span-2">
              {selectedTrace && (
                <TraceDetails trace={selectedTrace} evaluation={selectedEvaluation} />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Adversarial Scenario Generator Modal */}
      <ScenarioGeneratorModal
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
      />
    </div>
  );
}
