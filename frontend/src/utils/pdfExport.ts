import { jsPDF } from "jspdf";
import { Trace, EvaluationRecord } from "../types";

export function exportTracePDF(trace: Trace, evaluation?: EvaluationRecord): void {
  const doc = new jsPDF();
  let y = 20;

  // Header
  doc.setFontSize(22);
  doc.setTextColor(30, 41, 59);
  doc.text("AEGIS Agent Audit Report", 20, y);
  y += 8;

  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139);
  doc.text(`Generated on ${new Date().toLocaleString()} | Run ID: ${trace.run_id}`, 20, y);
  y += 12;

  // Metadata Section
  doc.setDrawColor(226, 232, 240);
  doc.line(20, y, 190, y);
  y += 8;

  doc.setFontSize(12);
  doc.setTextColor(15, 23, 42);
  doc.text(`Agent ID: ${trace.agent_id} (Version: ${trace.agent_version})`, 20, y);
  y += 6;
  doc.text(`Execution Status: ${trace.status.toUpperCase()}`, 20, y);
  y += 6;

  if (trace.metrics) {
    doc.text(
      `Latency: ${trace.metrics.latency_ms?.toFixed(0) || 0} ms | Tokens: ${(trace.metrics.input_tokens || 0) + (trace.metrics.output_tokens || 0)} | Cost: $${trace.metrics.estimated_cost?.toFixed(5) || "0.00"}`,
      20,
      y
    );
    y += 10;
  }

  // Evaluation Metrics
  if (evaluation) {
    doc.line(20, y, 190, y);
    y += 8;
    doc.setFontSize(14);
    doc.setTextColor(15, 23, 42);
    doc.text("Evaluation & Reliability Summary", 20, y);
    y += 7;

    doc.setFontSize(11);
    const scorePct = evaluation.overall_score !== null ? `${Math.round(evaluation.overall_score * 100)}%` : "N/A";
    doc.text(`Overall Reliability Score: ${scorePct} [Status: ${evaluation.reliability_status || "N/A"}]`, 20, y);
    y += 7;

    if (evaluation.evaluations && evaluation.evaluations.length > 0) {
      doc.setFontSize(10);
      doc.setTextColor(71, 85, 105);
      doc.text("Evaluator Breakdown:", 20, y);
      y += 6;

      for (const ev of evaluation.evaluations) {
        doc.text(
          `• ${ev.evaluator}: ${ev.verdict} (Score: ${Math.round(ev.score * 100)}%, Conf: ${Math.round(ev.confidence * 100)}%)`,
          24,
          y
        );
        y += 5;
        if (ev.summary) {
          doc.setTextColor(100, 116, 139);
          const splitSummary = doc.splitTextToSize(`  Summary: ${ev.summary}`, 160);
          doc.text(splitSummary, 26, y);
          y += splitSummary.length * 4.5 + 2;
          doc.setTextColor(71, 85, 105);
        }
      }
      y += 4;
    }
  }

  // Task & Output
  doc.line(20, y, 190, y);
  y += 8;
  doc.setFontSize(12);
  doc.setTextColor(15, 23, 42);
  doc.text("Task Input:", 20, y);
  y += 6;
  doc.setFontSize(9);
  doc.setTextColor(71, 85, 105);
  const taskText = typeof trace.task.input === "string" ? trace.task.input : JSON.stringify(trace.task.input, null, 2);
  const splitTask = doc.splitTextToSize(taskText, 170);
  doc.text(splitTask, 20, y);
  y += splitTask.length * 4 + 6;

  doc.setFontSize(12);
  doc.setTextColor(15, 23, 42);
  doc.text("Final Output:", 20, y);
  y += 6;
  doc.setFontSize(9);
  doc.setTextColor(71, 85, 105);
  const splitOutput = doc.splitTextToSize(trace.final_output || "No output recorded", 170);
  doc.text(splitOutput, 20, y);

  doc.save(`aegis-report-${trace.run_id}.pdf`);
}
