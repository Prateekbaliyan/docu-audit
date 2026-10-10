"use client";

import React, { useState, useEffect } from "react";
import { Shield, RefreshCw, Files, FileSpreadsheet, Download, CheckCircle2, AlertTriangle } from "lucide-react";
import { UploadZone } from "../components/UploadZone";
import { RiskGauge } from "../components/RiskGauge";
import { DualPaneViewer } from "../components/DualPaneViewer";
import { AnomalyChecklist } from "../components/AnomalyChecklist";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);
  const [auditData, setAuditData] = useState<any>(null);
  const [batchResults, setBatchResults] = useState<any[] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadSample("clean");
  }, []);

  const loadSample = async (sampleType: "clean" | "tampered") => {
    setIsAnalyzing(true);
    setErrorMsg(null);
    setBatchResults(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/samples/${sampleType}`);
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      const data = await res.json();
      setAuditData(data);
    } catch (err: any) {
      setErrorMsg(`Failed to connect to backend: ${err.message}. Ensure FastAPI server is running on port 8000.`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileUpload = async (filesInput: FileList | File[]) => {
    setIsAnalyzing(true);
    setErrorMsg(null);

    const fileList = Array.from(filesInput);

    if (fileList.length === 1) {
      // Single Document Processing
      setBatchResults(null);
      try {
        const formData = new FormData();
        formData.append("file", fileList[0]);

        const res = await fetch(`${API_BASE_URL}/api/audit`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Server error ${res.status}`);
        const data = await res.json();
        setAuditData(data);
      } catch (err: any) {
        setErrorMsg(`Upload failed: ${err.message}`);
      } finally {
        setIsAnalyzing(false);
      }
    } else {
      // Batch Multi-Document Processing
      try {
        const formData = new FormData();
        fileList.forEach((f) => formData.append("files", f));

        const res = await fetch(`${API_BASE_URL}/api/audit/batch`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Batch audit error ${res.status}`);
        const batchData = await res.json();
        setBatchResults(batchData.results);
        if (batchData.results.length > 0) {
          setAuditData(batchData.results[0]);
        }
      } catch (err: any) {
        setErrorMsg(`Batch processing failed: ${err.message}`);
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  const handleExportBatchCsv = async () => {
    if (!batchResults) return;
    try {
      const summaries = batchResults.map((b) => b.summary);
      const res = await fetch(`${API_BASE_URL}/api/export/batch-csv`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summaries }),
      });

      if (!res.ok) throw new Error("Failed to export CSV summary");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "DocuAudit_Batch_Summary.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    }
  };

  const handleExportPdf = async () => {
    if (!auditData?.summary) return;
    setIsExportingPdf(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/export/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary: auditData.summary }),
      });

      if (!res.ok) throw new Error("Failed to generate PDF report");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DocuAudit_Report_${auditData.summary.file_name || "Doc"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleExportJson = () => {
    if (!auditData) return;
    const jsonStr = JSON.stringify(auditData, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DocuAudit_Evidence_${auditData.summary?.file_name || "Doc"}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-blue-600 selection:text-white">
      {/* Header Bar */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg text-white shadow-2xs">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-slate-900">DocuAudit</h1>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200 rounded-md">
                  v2.5 Enterprise
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Digital Document Forensics & Tampering Detection</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => loadSample("clean")}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 rounded-lg transition-all shadow-2xs"
            >
              <RefreshCw className="w-3.5 h-3.5 text-slate-500" /> Reload Sample
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Error Alert */}
        {errorMsg && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs font-medium flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-xs underline font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {/* Document Intake Zone */}
        <UploadZone
          onFileUpload={handleFileUpload}
          onSelectSample={loadSample}
          isAnalyzing={isAnalyzing}
        />

        {/* Batch Audit Queue Summary Banner if multiple files uploaded */}
        {batchResults && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Files className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Batch Audit Queue Summary ({batchResults.length} Files Processed)
                </h3>
              </div>
              <button
                onClick={handleExportBatchCsv}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-all"
              >
                <FileSpreadsheet className="w-4 h-4" /> Export Batch CSV Summary
              </button>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider border-b border-slate-200">
                    <th className="py-2.5 px-4">Document</th>
                    <th className="py-2.5 px-4">Tamper Score</th>
                    <th className="py-2.5 px-4">Rating</th>
                    <th className="py-2.5 px-4">Flagged Tests</th>
                    <th className="py-2.5 px-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {batchResults.map((res, i) => (
                    <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-2.5 px-4 font-semibold text-slate-800">{res.summary.file_name}</td>
                      <td className="py-2.5 px-4 font-bold">
                        <span className={res.summary.tamper_score >= 70 ? "text-rose-600" : res.summary.tamper_score >= 25 ? "text-amber-600" : "text-emerald-600"}>
                          {res.summary.tamper_score}%
                        </span>
                      </td>
                      <td className="py-2.5 px-4 uppercase font-semibold text-[11px]">{res.summary.rating}</td>
                      <td className="py-2.5 px-4 text-slate-600">{res.summary.flagged_count} flagged</td>
                      <td className="py-2.5 px-4">
                        <button
                          onClick={() => setAuditData(res)}
                          className="text-blue-600 font-semibold hover:underline"
                        >
                          Inspect Detail
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Single Selected Document Inspection Dashboard */}
        {auditData && (
          <>
            <RiskGauge
              score={auditData.summary.tamper_score}
              rating={auditData.summary.rating}
              riskLabel={auditData.summary.risk_label}
              flaggedCount={auditData.summary.flagged_count}
              passedCount={auditData.summary.passed_count}
            />

            <DualPaneViewer
              originalImageB64={auditData.document.original_image_b64}
              elaImageB64={auditData.layers.ela.ela_image_b64}
              noiseImageB64={auditData.layers.noise.noise_image_b64}
              cmfdImageB64={auditData.layers.cmfd.cmfd_image_b64}
              fontAnomalyBoxes={auditData.layers.pdf_structure.font_anomaly_boxes}
              elaAnomalyBoxes={auditData.layers.ela.anomaly_boxes}
              currentPage={auditData.document.current_page}
              totalPages={auditData.document.total_pages}
              exifData={auditData.layers.exif}
              signaturesData={auditData.layers.signatures}
            />

            <AnomalyChecklist
              sha256={auditData.summary.sha256}
              fileName={auditData.summary.file_name}
              findings={auditData.summary.findings}
              onExportPdf={handleExportPdf}
              onExportJson={handleExportJson}
              isExportingPdf={isExportingPdf}
            />
          </>
        )}
      </div>
    </main>
  );
}
