"use client";

import React, { useRef } from "react";
import { Activity, Upload, Sparkles, RefreshCw } from "lucide-react";

interface HeaderProps {
  connected: boolean;
  uploading: boolean;
  uploadStatus: string | null;
  onFileUpload: (file: File) => Promise<void>;
  onOpenScenarioModal: () => void;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  connected,
  uploading,
  uploadStatus,
  onFileUpload,
  onOpenScenarioModal,
  onRefresh,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0]);
      e.target.value = "";
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg shadow-inner">
            <Activity className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">AEGIS Engine</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono border border-slate-700">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Agent Evaluation, Reliability & Observability Engine
            </p>
          </div>
        </div>

        {/* Actions & Status */}
        <div className="flex items-center gap-3">
          {/* Scenario Generator Button */}
          <button
            onClick={onOpenScenarioModal}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition-all cursor-pointer shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            Adversarial Scenarios
          </button>

          {/* Upload Trace Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".json,.jsonl"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer shadow-sm ${
              uploading
                ? "bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 text-white border-indigo-500 hover:shadow-indigo-500/20"
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            {uploading ? "Evaluating..." : "Upload Trace (.json/.jsonl)"}
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            title="Refresh traces"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Connection Status indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"
              }`}
            />
            <span className="text-xs font-mono text-slate-300">
              {connected ? "LIVE WS" : "OFFLINE"}
            </span>
          </div>
        </div>
      </div>

      {/* Upload status banner if active */}
      {uploadStatus && (
        <div className="bg-indigo-950/70 border-t border-b border-indigo-500/20 px-6 py-2 text-center">
          <span className="text-xs font-mono text-indigo-300">{uploadStatus}</span>
        </div>
      )}
    </header>
  );
};
