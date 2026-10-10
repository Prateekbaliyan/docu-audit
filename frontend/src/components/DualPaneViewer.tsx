"use client";

import React, { useState } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sliders,
  Eye,
  Activity,
  Cpu,
  Type,
  GitCommit,
  Layers,
  Search,
  Camera,
  FileCheck2,
} from "lucide-react";
import { useSynchronizedZoomPan } from "../hooks/useSynchronizedZoomPan";

export type LayerMode = "normal" | "ela" | "noise" | "font" | "cmfd" | "exif" | "signatures";

interface DualPaneViewerProps {
  originalImageB64: string;
  elaImageB64?: string;
  noiseImageB64?: string;
  cmfdImageB64?: string;
  fontAnomalyBoxes?: Array<{
    x_pct: number;
    y_pct: number;
    w_pct: number;
    h_pct: number;
    text: string;
    reason: string;
  }>;
  elaAnomalyBoxes?: Array<{
    x: number;
    y: number;
    w: number;
    h: number;
    variance: number;
  }>;
  currentPage: number;
  totalPages: number;
  exifData?: any;
  signaturesData?: any;
}

export const DualPaneViewer: React.FC<DualPaneViewerProps> = ({
  originalImageB64,
  elaImageB64,
  noiseImageB64,
  cmfdImageB64,
  fontAnomalyBoxes = [],
  elaAnomalyBoxes = [],
  currentPage,
  totalPages,
  exifData,
  signaturesData,
}) => {
  const [activeLayer, setActiveLayer] = useState<LayerMode>("ela");
  const [overlayOpacity, setOverlayOpacity] = useState<number>(0.85);
  const [hoveredBox, setHoveredBox] = useState<string | null>(null);
  
  // Interactive 4x Pixel Magnifier Loupe state
  const [isMagnifierActive, setIsMagnifierActive] = useState<boolean>(false);
  const [magnifierPos, setMagnifierPos] = useState<{ x: number; y: number; px: number; py: number; show: boolean }>({
    x: 0,
    y: 0,
    px: 0,
    py: 0,
    show: false,
  });

  const { transform, zoomIn, zoomOut, resetZoom, bindContainer } =
    useSynchronizedZoomPan(1.0);

  const getOverlayImage = () => {
    switch (activeLayer) {
      case "ela":
        return elaImageB64 || originalImageB64;
      case "noise":
        return noiseImageB64 || originalImageB64;
      case "cmfd":
        return cmfdImageB64 || originalImageB64;
      default:
        return originalImageB64;
    }
  };

  const overlayImg = getOverlayImage();

  const handleLoupeMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isMagnifierActive) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const px = Math.min(Math.max((x / rect.width) * 100, 0), 100);
    const py = Math.min(Math.max((y / rect.height) * 100, 0), 100);
    setMagnifierPos({ x, y, px, py, show: true });
  };

  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
      {/* Top Toolbar: Layer Selectors & Zoom Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        {/* Layer Mode Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200/80">
          <button
            onClick={() => setActiveLayer("normal")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "normal"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Eye className="w-3.5 h-3.5" /> Normal
          </button>

          <button
            onClick={() => setActiveLayer("ela")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "ela"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-blue-600" /> ELA Heatmap
          </button>

          <button
            onClick={() => setActiveLayer("noise")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "noise"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-amber-600" /> Noise Print
          </button>

          <button
            onClick={() => setActiveLayer("font")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "font"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Type className="w-3.5 h-3.5 text-rose-600" /> Font & Baseline
          </button>

          <button
            onClick={() => setActiveLayer("cmfd")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "cmfd"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <GitCommit className="w-3.5 h-3.5 text-purple-600" /> Copy-Move Vectors
          </button>

          <button
            onClick={() => setActiveLayer("exif")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "exif"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Camera className="w-3.5 h-3.5 text-emerald-600" /> Camera EXIF
          </button>

          <button
            onClick={() => setActiveLayer("signatures")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeLayer === "signatures"
                ? "bg-white text-blue-600 shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileCheck2 className="w-3.5 h-3.5 text-cyan-600" /> Digital Signatures
          </button>
        </div>

        {/* Opacity Slider & Magnifier Glass Toggle & Zoom Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* 4x Magnifier Loupe Glass Toggle */}
          <button
            onClick={() => setIsMagnifierActive(!isMagnifierActive)}
            className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg border transition-all ${
              isMagnifierActive
                ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
            }`}
          >
            <Search className="w-3.5 h-3.5" /> 4x Magnifier Glass
          </button>

          {activeLayer !== "normal" && activeLayer !== "exif" && activeLayer !== "signatures" && (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1 rounded-lg">
              <Sliders className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-[11px] font-semibold text-slate-600">Opacity</span>
              <input
                type="range"
                min="0.2"
                max="1.0"
                step="0.05"
                value={overlayOpacity}
                onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                className="w-20 accent-blue-600 cursor-pointer"
              />
            </div>
          )}

          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 p-1 rounded-lg">
            <button
              onClick={zoomIn}
              title="Zoom In"
              className="p-1 hover:bg-slate-200 text-slate-700 rounded transition-all"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={zoomOut}
              title="Zoom Out"
              className="p-1 hover:bg-slate-200 text-slate-700 rounded transition-all"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={resetZoom}
              title="Reset Zoom"
              className="p-1 hover:bg-slate-200 text-slate-700 rounded transition-all"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <span className="text-xs font-mono text-slate-600 px-2 border-l border-slate-200">
              {Math.round(transform.scale * 100)}%
            </span>
          </div>

          <div className="text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg">
            Page {currentPage} of {totalPages}
          </div>
        </div>
      </div>

      {/* Dual Pane Workspace */}
      <div
        {...bindContainer}
        className="relative grid grid-cols-1 lg:grid-cols-2 gap-4 h-[580px] bg-slate-100 rounded-lg overflow-hidden cursor-grab active:cursor-grabbing border border-slate-200"
      >
        {/* LEFT PANE: Original Pristine Image */}
        <div
          onMouseMove={handleLoupeMouseMove}
          onMouseLeave={() => setMagnifierPos((p) => ({ ...p, show: false }))}
          className="relative w-full h-full overflow-hidden flex items-center justify-center bg-slate-200/50 border-r border-slate-300/60"
        >
          <div className="absolute top-3 left-3 bg-white/90 border border-slate-300 text-slate-800 text-xs font-semibold px-2.5 py-1 rounded-md z-10 shadow-2xs backdrop-blur-xs flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Original Document
          </div>

          <div
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
              transition: "transform 0.05s ease-out",
            }}
            className="max-w-full max-h-full flex items-center justify-center p-4"
          >
            {originalImageB64 ? (
              <img
                src={originalImageB64}
                alt="Original Document"
                className="max-w-full max-h-[520px] object-contain shadow-md rounded border border-slate-300 bg-white"
                draggable={false}
              />
            ) : (
              <div className="text-slate-400 text-sm">No document loaded</div>
            )}
          </div>

          {/* Interactive 4x Pixel Magnifier Loupe Lens */}
          {isMagnifierActive && magnifierPos.show && originalImageB64 && (
            <div
              style={{
                left: `${magnifierPos.x - 75}px`,
                top: `${magnifierPos.y - 75}px`,
                backgroundImage: `url(${originalImageB64})`,
                backgroundSize: "400%",
                backgroundPosition: `${magnifierPos.px}% ${magnifierPos.py}%`,
              }}
              className="absolute w-36 h-36 rounded-full border-4 border-blue-600 shadow-2xl pointer-events-none z-30 bg-no-repeat bg-white overflow-hidden"
            >
              <div className="absolute bottom-1 right-2 text-[9px] font-bold text-blue-600 bg-white/90 px-1 rounded shadow">
                4x LOUPE
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANE: Forensic Layer Overlay or EXIF / Signature Info */}
        <div className="relative w-full h-full overflow-hidden flex items-center justify-center bg-slate-200/50">
          <div className="absolute top-3 left-3 bg-white/90 border border-slate-300 text-slate-800 text-xs font-semibold px-2.5 py-1 rounded-md z-10 shadow-2xs backdrop-blur-xs flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            Forensic View:{" "}
            <span className="uppercase text-blue-700 font-bold ml-1">{activeLayer}</span>
          </div>

          {activeLayer === "exif" ? (
            <div className="p-6 bg-white border border-slate-300 rounded-lg shadow-md max-w-md text-xs space-y-3">
              <h4 className="font-bold text-slate-900 border-b border-slate-200 pb-2 flex items-center gap-1.5">
                <Camera className="w-4 h-4 text-emerald-600" /> Camera Hardware & EXIF Profile
              </h4>
              <p className="text-slate-600">{exifData?.reason || "No EXIF camera metadata embedded"}</p>
              {exifData?.has_exif && (
                <div className="space-y-1 font-mono text-slate-700">
                  <div><b>Camera Make:</b> {exifData.camera_make || "N/A"}</div>
                  <div><b>Camera Model:</b> {exifData.camera_model || "N/A"}</div>
                  <div><b>Software:</b> {exifData.software || "N/A"}</div>
                  <div><b>Date Captured:</b> {exifData.capture_date || "N/A"}</div>
                </div>
              )}
            </div>
          ) : activeLayer === "signatures" ? (
            <div className="p-6 bg-white border border-slate-300 rounded-lg shadow-md max-w-md text-xs space-y-3">
              <h4 className="font-bold text-slate-900 border-b border-slate-200 pb-2 flex items-center gap-1.5">
                <FileCheck2 className="w-4 h-4 text-cyan-600" /> PDF Electronic Signatures (PKCS#7)
              </h4>
              <p className="text-slate-600">{signaturesData?.status_text || "No electronic signatures found"}</p>
              {signaturesData?.has_signatures && (
                <div className="space-y-1 font-mono text-slate-700">
                  <div><b>Signature Count:</b> {signaturesData.signature_count}</div>
                  <div><b>Post-Signing Alterations:</b> {signaturesData.post_signing_alteration ? "CRITICAL ALERT" : "None"}</div>
                </div>
              )}
            </div>
          ) : (
            <div
              style={{
                transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
                transition: "transform 0.05s ease-out",
              }}
              className="relative max-w-full max-h-full flex items-center justify-center p-4"
            >
              {overlayImg ? (
                <div className="relative inline-block">
                  <img
                    src={overlayImg}
                    alt="Forensic Overlay Layer"
                    style={{ opacity: activeLayer === "normal" ? 1.0 : overlayOpacity }}
                    className="max-w-full max-h-[520px] object-contain shadow-md rounded border border-slate-300 bg-white transition-opacity duration-200"
                    draggable={false}
                  />

                  {activeLayer === "font" &&
                    fontAnomalyBoxes.map((box, i) => (
                      <div
                        key={i}
                        onMouseEnter={() => setHoveredBox(box.reason)}
                        onMouseLeave={() => setHoveredBox(null)}
                        style={{
                          left: `${box.x_pct}%`,
                          top: `${box.y_pct}%`,
                          width: `${box.w_pct}%`,
                          height: `${box.h_pct}%`,
                        }}
                        className="absolute border-2 border-rose-600 bg-rose-500/20 rounded cursor-pointer transition-all hover:bg-rose-500/40 hover:scale-105 z-20"
                      >
                        <span className="absolute -top-5 left-0 bg-rose-600 text-white text-[9px] font-bold px-1 rounded shadow">
                          FONT JUMP: {box.text}
                        </span>
                      </div>
                    ))}

                  {hoveredBox && (
                    <div className="absolute top-2 right-2 bg-white border border-rose-200 text-rose-800 text-xs p-2.5 rounded-lg shadow-lg z-30 max-w-xs">
                      {hoveredBox}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-slate-400 text-sm">No forensic overlay available</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
