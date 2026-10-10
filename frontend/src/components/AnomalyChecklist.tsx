"use client";

import React from "react";
import { Download, FileJson, CheckCircle2, AlertTriangle, Key, ShieldCheck } from "lucide-react";

interface Finding {
  test: string;
  status: "PASS" | "FLAGGED";
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: string;
  rationale: string;
}

interface AnomalyChecklistProps {
  sha256: string;
  fileName: string;
  findings: Finding[];
  onExportPdf: () => void;
  onExportJson: () => void;
  isExportingPdf?: boolean;
}

export const AnomalyChecklist: React.FC<AnomalyChecklistProps> = ({
  sha256,
  fileName,
  findings,
  onExportPdf,
  onExportJson,
  isExportingPdf,
}) => {
  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-6">
      {/* Header & Export Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            Diagnostic Forensic Test Evidence
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated multi-layer verification matrix for document chain-of-custody.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onExportJson}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 transition-all"
          >
            <FileJson className="w-4 h-4 text-slate-600" />
            Export JSON
          </button>

          <button
            onClick={onExportPdf}
            disabled={isExportingPdf}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-all disabled:opacity-50 shadow-2xs"
          >
            <Download className="w-4 h-4" />
            {isExportingPdf ? "Generating PDF..." : "Export Forensic Report (PDF)"}
          </button>
        </div>
      </div>

      {/* Cryptographic SHA-256 Hash Badge */}
      <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs font-mono text-slate-700 overflow-x-auto">
        <Key className="w-4 h-4 text-amber-600 shrink-0" />
        <span className="text-slate-500 font-sans font-semibold shrink-0">SHA-256 Hash:</span>
        <span className="text-slate-800 font-mono tracking-tight select-all">{sha256 || "N/A"}</span>
      </div>

      {/* Findings Breakdown Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-slate-600 text-[11px] font-bold uppercase tracking-wider border-b border-slate-200">
              <th className="py-3 px-4">Forensic Module</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Conf.</th>
              <th className="py-3 px-4">Diagnostic Rationale & Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
            {findings.map((f, i) => {
              const isFlagged = f.status === "FLAGGED";
              return (
                <tr
                  key={i}
                  className={`transition-colors ${
                    isFlagged ? "bg-rose-50/40 hover:bg-rose-50/70" : "hover:bg-slate-50/50"
                  }`}
                >
                  <td className="py-3.5 px-4 font-semibold text-slate-900">{f.test}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold uppercase ${
                        isFlagged
                          ? "bg-rose-100 text-rose-800 border border-rose-200"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                      }`}
                    >
                      {isFlagged ? (
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      )}
                      {f.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-500">{f.confidence}</td>
                  <td className="py-3.5 px-4 text-slate-600 leading-relaxed">{f.rationale}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
