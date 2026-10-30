import { useState, useEffect, useCallback } from "react";
import { Trace, EvaluationRecord, WebSocketMessage } from "../types";
import { api, WS_URL } from "../services/api";

export interface UseTraceStreamState {
  traces: Trace[];
  evaluations: Record<string, EvaluationRecord>;
  loading: boolean;
  connected: boolean;
  error: string | null;
  selectedRunId: string | null;
  setSelectedRunId: (runId: string | null) => void;
  refetch: () => Promise<void>;
  uploadTraceFile: (file: File) => Promise<void>;
  uploading: boolean;
  uploadStatus: string | null;
}

export function useTraceStream(): UseTraceStreamState {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [evaluations, setEvaluations] = useState<Record<string, EvaluationRecord>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [connected, setConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const fetchHistoricalData = useCallback(async () => {
    try {
      setError(null);
      const [fetchedTraces, fetchedEvals] = await Promise.all([
        api.getTraces(),
        api.getEvaluations(),
      ]);

      setTraces(fetchedTraces);
      const byRunId: Record<string, EvaluationRecord> = {};
      for (const e of fetchedEvals) {
        byRunId[e.run_id] = e;
      }
      setEvaluations(byRunId);

      if (fetchedTraces.length > 0 && !selectedRunId) {
        setSelectedRunId(fetchedTraces[0].run_id);
      }
    } catch (err: any) {
      console.error("Error loading historical trace records:", err);
      setError(err.message || "Failed to load trace data from engine.");
    } finally {
      setLoading(false);
    }
  }, [selectedRunId]);

  useEffect(() => {
    fetchHistoricalData();

    let ws: WebSocket | null = null;
    let retryTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          setConnected(true);
        };

        ws.onclose = () => {
          setConnected(false);
          // Auto-reconnect after 3 seconds
          retryTimeout = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (e) => {
          console.warn("WebSocket stream notice:", e);
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            if (message.event_type === "TRACE_INGESTED") {
              setTraces((prev) => [message.data, ...prev.filter((t) => t.run_id !== message.data.run_id)]);
              setSelectedRunId(message.data.run_id);
            } else if (message.event_type === "REPORT_READY") {
              const record: EvaluationRecord = message.data;
              setEvaluations((prev) => ({ ...prev, [record.run_id]: record }));
            }
          } catch (jsonErr) {
            console.error("Failed to parse live WS message:", jsonErr);
          }
        };
      } catch (e) {
        console.warn("Could not initiate WebSocket:", e);
        retryTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      clearTimeout(retryTimeout);
    };
  }, [fetchHistoricalData]);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus(`Uploading & evaluating ${file.name}...`);
    try {
      const response = await api.uploadTraceFile(file);
      setUploadStatus(`Evaluated ${response.traces_evaluated_count} trace(s) from ${file.name}`);
      setTimeout(() => setUploadStatus(null), 4000);
      await fetchHistoricalData();
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message || "Unknown error"}`);
      setTimeout(() => setUploadStatus(null), 5000);
      throw err;
    } finally {
      setUploading(false);
    }
  };

  return {
    traces,
    evaluations,
    loading,
    connected,
    error,
    selectedRunId,
    setSelectedRunId,
    refetch: fetchHistoricalData,
    uploadTraceFile: handleFileUpload,
    uploading,
    uploadStatus,
  };
}
