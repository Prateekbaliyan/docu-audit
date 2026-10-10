"use client";

import React, { useRef, useState } from "react";
import { Upload, FileText, AlertTriangle, CheckCircle2, Loader2, FileCheck, Files } from "lucide-react";

interface UploadZoneProps {
  onFileUpload: (files: FileList | File[]) => void;
  onSelectSample: (sampleType: "clean" | "tampered") => void;
  isAnalyzing: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileUpload,
  onSelectSample,
  isAnalyzing,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
    }
  };

  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Drag & Drop Box supporting multiple file drop */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex-1 w-full border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200 ${
            isDragOver
              ? "border-blue-600 bg-blue-50/50"
              : "border-slate-300 bg-slate-50/50 hover:border-blue-500 hover:bg-slate-50"
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            multiple
            className="hidden"
          />
          <div className="flex flex-col items-center gap-2.5">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-full border border-blue-100">
              {isAnalyzing ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Upload className="w-6 h-6" />
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 flex items-center justify-center gap-1.5">
                {isAnalyzing ? "Executing Forensic Audit..." : "Click to upload single or multiple documents (Bulk Batch Audit)"}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Supports PDF, PNG, JPG, or TIFF (Drag multiple files for batch mode)
              </p>
            </div>
          </div>
        </div>

        {/* Quick Sample Selector */}
        <div className="w-full md:w-auto flex flex-col gap-2.5 min-w-[280px]">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <FileCheck className="w-3.5 h-3.5 text-blue-600" />
            Try Sample Documents
          </div>

          <button
            onClick={() => onSelectSample("clean")}
            disabled={isAnalyzing}
            className="group flex items-center justify-between px-3.5 py-2.5 bg-white hover:bg-emerald-50/50 border border-slate-200 hover:border-emerald-300 rounded-lg transition-all text-left shadow-2xs disabled:opacity-50"
          >
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <div className="text-xs font-semibold text-slate-800 group-hover:text-emerald-900">
                  Clean Bank Statement
                </div>
                <div className="text-[11px] text-slate-500">Pristine document</div>
              </div>
            </div>
            <FileText className="w-4 h-4 text-slate-400 group-hover:text-emerald-600" />
          </button>

          <button
            onClick={() => onSelectSample("tampered")}
            disabled={isAnalyzing}
            className="group flex items-center justify-between px-3.5 py-2.5 bg-white hover:bg-rose-50/50 border border-slate-200 hover:border-rose-300 rounded-lg transition-all text-left shadow-2xs disabled:opacity-50"
          >
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <div>
                <div className="text-xs font-semibold text-slate-800 group-hover:text-rose-900">
                  Tampered Invoice
                </div>
                <div className="text-[11px] text-slate-500">Modified font + math error</div>
              </div>
            </div>
            <FileText className="w-4 h-4 text-slate-400 group-hover:text-rose-600" />
          </button>
        </div>
      </div>
    </div>
  );
};
