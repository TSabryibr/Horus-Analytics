"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";

interface SRLevel {
  price: number;
  strength: number; // 0-1
  type: "SUPPORT" | "RESISTANCE";
  label?: string;
  members?: number;
}

interface SupportResistanceRadarProps {
  currentPrice: number;
  levels: SRLevel[];
  mode?: "single" | "scope";
  leadTicker?: string | null;
}

export const SupportResistanceRadar: React.FC<SupportResistanceRadarProps> = ({
  currentPrice,
  levels,
  mode = "single",
  leadTicker = null,
}) => {
  const sortedLevels = useMemo(() => {
    return [...levels].sort((a, b) => Math.abs(a.price - currentPrice) - Math.abs(b.price - currentPrice));
  }, [levels, currentPrice]);

  const maxDelta = Math.max(
    currentPrice * 0.15,
    ...sortedLevels.map((level) => Math.abs(level.price - currentPrice)),
    1
  );

  const legendItems =
    mode === "scope"
      ? [
          { label: "BASKET SUPPORT", color: "#22d3ee" },
          { label: "BASKET RESISTANCE", color: "#f43f5e" },
          { label: leadTicker ? `LEAD ${leadTicker}` : "LEAD TICKER", color: "#fbbf24" },
        ]
      : [
          { label: "SUP", color: "#22d3ee" },
          { label: "RES", color: "#f43f5e" },
      ];
  const supportLabels = sortedLevels
    .filter((level) => level.type === "SUPPORT")
    .slice(0, 2)
    .map((level) => level.price.toFixed(2));
  const resistanceLabels = sortedLevels
    .filter((level) => level.type === "RESISTANCE")
    .slice(0, 2)
    .map((level) => level.price.toFixed(2));

  return (
    <div className="relative w-full aspect-square bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden font-mono text-[10px]">
      {/* Background Grid */}
      <svg viewBox="0 0 200 200" className="w-full h-full">
        {/* Radar Rings */}
        <circle cx="100" cy="100" r="30" fill="none" stroke="#1e293b" strokeDasharray="2 2" />
        <circle cx="100" cy="100" r="60" fill="none" stroke="#1e293b" strokeDasharray="2 2" />
        <circle cx="100" cy="100" r="90" fill="none" stroke="#1e293b" strokeDasharray="2 2" />
        
        {/* Crosshair */}
        <line x1="100" y1="10" x2="100" y2="190" stroke="#1e293b" strokeWidth="1" />
        <line x1="10" y1="100" x2="190" y2="100" stroke="#1e293b" strokeWidth="1" />

        {/* Level Markers */}
        {sortedLevels.map((level, i) => {
          const delta = level.price - currentPrice;
          const normalizedDelta = (delta / maxDelta) * 90;
          const y = 100 - normalizedDelta;
          
          const isSupport = level.type === "SUPPORT";
          const color = isSupport ? "#22d3ee" : "#f43f5e"; // Cyan vs Rose
          
          return (
            <motion.g
              key={i}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              {/* Horizontal Line on Radar */}
              <line 
                x1="40" y1={y} x2="160" y2={y} 
                stroke={color} 
                strokeWidth="1" 
                strokeOpacity={level.strength * 0.5} 
              />
              {/* Marker Dot */}
              <circle cx="100" cy={y} r="3" fill={color} />
              
              {/* Text Label */}
              <text 
                x="145" y={y + 3} 
                fill={color} 
                className="font-bold"
              >
                {level.price.toFixed(2)}
              </text>
              {mode === "scope" && level.members ? (
                <text
                  x="145"
                  y={y + 10}
                  fill="#64748b"
                  className="text-[7px]"
                >
                  {level.members}x cluster
                </text>
              ) : null}
            </motion.g>
          );
        })}

        {/* Current Price Indicator */}
        <circle cx="100" cy="100" r={mode === "scope" ? 5 : 4} fill="#fbbf24" stroke="#000" strokeWidth="1" />
        <text x="105" y="95" fill="#fbbf24" className="font-bold text-[12px]">
          {currentPrice.toFixed(2)}
        </text>
        {mode === "scope" && leadTicker ? (
          <text x="105" y="104" fill="#f8fafc" className="text-[7px] font-bold uppercase">
            {leadTicker}
          </text>
        ) : null}

        {/* Legend */}
        {legendItems.map((item, index) => (
          <text key={item.label} x="10" y={20 + index * 12} fill={item.color}>
            {item.label}
          </text>
        ))}
      </svg>

      {/* Perimeter Glow */}
      <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_20px_rgba(30,41,59,0.5)]" />
      
      {/* Tactical Label */}
      <div className="absolute top-2 right-2 px-2 py-0.5 bg-slate-900 border border-slate-700 text-slate-400 uppercase tracking-widest text-[8px]">
        {mode === "scope" ? "S/R Radar v2.0" : "S/R Radar v1.0"}
      </div>

      <div className="absolute inset-x-2 bottom-2 grid grid-cols-3 gap-1 rounded border border-slate-700/80 bg-slate-950/88 p-2 text-[8px] uppercase tracking-[0.16em] text-slate-400 shadow-[0_12px_30px_rgba(2,6,23,0.45)]">
        <div>
          <div className="text-slate-600">Current</div>
          <div className="mt-1 text-[10px] font-black tracking-normal text-amber-300">{currentPrice.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-cyan-400/70">Support</div>
          <div className="mt-1 text-[10px] font-black tracking-normal text-cyan-300">
            {supportLabels.length > 0 ? supportLabels.join(" / ") : "--"}
          </div>
        </div>
        <div>
          <div className="text-rose-400/70">Resistance</div>
          <div className="mt-1 text-[10px] font-black tracking-normal text-rose-300">
            {resistanceLabels.length > 0 ? resistanceLabels.join(" / ") : "--"}
          </div>
        </div>
      </div>
    </div>
  );
};
