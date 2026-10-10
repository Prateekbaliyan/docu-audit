"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, AlertOctagon, Activity } from "lucide-react";

interface RiskGaugeProps {
  score: number;
  rating: string;
  riskLabel: string;
  flaggedCount: number;
  passedCount: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  rating,
  riskLabel,
  flaggedCount,
  passedCount,
}) => {
  const getTheme = () => {
    if (score >= 70) {
      return {
        stroke: "#dc2626", // Red-600
        bgBadge: "bg-rose-50 text-rose-700 border-rose-200",
        icon: <AlertOctagon className="w-5 h-5 text-rose-600" />,
      };
    }
    if (score >= 25) {
      return {
        stroke: "#d97706", // Amber-600
        bgBadge: "bg-amber-50 text-amber-700 border-amber-200",
        icon: <ShieldAlert className="w-5 h-5 text-amber-600" />,
      };
    }
    return {
      stroke: "#16a34a", // Green-600
      bgBadge: "bg-emerald-50 text-emerald-700 border-emerald-200",
      icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
    };
  };

  const theme = getTheme();
  const radius = 55;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
      {/* Gauge & Score Circular Display */}
      <div className="flex items-center gap-6">
        <div className="relative w-32 h-32 flex items-center justify-center shrink-0">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 130 130">
            {/* Background Track */}
            <circle
              cx="65"
              cy="65"
              r={radius}
              stroke="#f1f5f9"
              strokeWidth="10"
              fill="transparent"
            />
            {/* Progress Arc */}
            <circle
              cx="65"
              cy="65"
              r={radius}
              stroke={theme.stroke}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-bold tracking-tight text-slate-900">
              {score}%
            </span>
            <span className="text-[10px] uppercase font-semibold text-slate-400">
              Tamper Score
            </span>
          </div>
        </div>

        {/* Diagnostic Status Badge & Label */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            {theme.icon}
            <span className={`px-2.5 py-0.5 text-xs font-semibold uppercase rounded-md border ${theme.bgBadge}`}>
              {rating.replace("_", " ")}
            </span>
          </div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">
            {riskLabel}
          </h2>
          <p className="text-xs text-slate-500 max-w-sm">
            Automated multi-spectral vision & structural inspection analysis score.
          </p>
        </div>
      </div>

      {/* Passed vs Flagged Counters */}
      <div className="flex items-center gap-6 bg-slate-50 border border-slate-200 px-6 py-3.5 rounded-lg shrink-0 w-full md:w-auto justify-around">
        <div className="text-center">
          <div className="text-xs font-medium text-slate-500">Flagged</div>
          <div className="text-xl font-bold text-rose-600">{flaggedCount}</div>
        </div>
        <div className="h-7 w-px bg-slate-200" />
        <div className="text-center">
          <div className="text-xs font-medium text-slate-500">Passed</div>
          <div className="text-xl font-bold text-emerald-600">{passedCount}</div>
        </div>
        <div className="h-7 w-px bg-slate-200" />
        <div className="text-center">
          <div className="text-xs font-medium text-slate-500 flex items-center gap-1 justify-center">
            <Activity className="w-3 h-3 text-slate-400" /> Total
          </div>
          <div className="text-xl font-bold text-slate-800">{flaggedCount + passedCount}</div>
        </div>
      </div>
    </div>
  );
};
