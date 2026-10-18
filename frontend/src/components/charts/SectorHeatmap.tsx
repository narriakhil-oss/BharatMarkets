"use client";

import { ResponsiveContainer, Treemap } from "recharts";
import { SectorPerformance } from "@/types/market";

interface SectorHeatmapProps {
  sectors: SectorPerformance[];
  activePeriod: string;
  onPeriodChange: (p: string) => void;
}

function getHeatmapColor(pct: number): string {
  if (pct >= 3.0) return "#00dc82";
  if (pct >= 1.5) return "#059669";
  if (pct > 0.05) return "#047857";
  if (pct >= -0.05) return "#3f3f46";
  if (pct > -1.5) return "#991b1b";
  if (pct > -3.0) return "#dc2626";
  return "#ef4444";
}

/* eslint-disable @typescript-eslint/no-explicit-any */
const CustomTreemapCell = (props: any) => {
  const { x = 0, y = 0, width = 0, height = 0, name = "", change_pct = 0 } = props;
  const isSmall = width < 65 || height < 40;
  const isTiny = width < 40 || height < 25;
  const color = getHeatmapColor(change_pct);

  if (isTiny) {
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={color} stroke="#09090b" strokeWidth={2} rx={4} />
      </g>
    );
  }

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={color} stroke="#09090b" strokeWidth={2} rx={4} className="transition-opacity duration-200 hover:opacity-90" />
      <text x={x + width / 2} y={y + height / 2 - (isSmall ? 0 : 8)} textAnchor="middle" dominantBaseline="central" fill="#ffffff" fontSize={isSmall ? 10 : 12} fontWeight={600} className="pointer-events-none select-none">
        {name.length > 12 && isSmall ? `${name.slice(0, 10)}…` : name}
      </text>
      {!isSmall && (
        <text x={x + width / 2} y={y + height / 2 + 10} textAnchor="middle" dominantBaseline="central" fill="#ffffff" fontSize={11} fontWeight={500} fontFamily="monospace" className="pointer-events-none select-none opacity-90">
          {change_pct > 0 ? "+" : ""}{change_pct.toFixed(2)}%
        </text>
      )}
    </g>
  );
};

export function SectorHeatmap({ sectors, activePeriod, onPeriodChange }: SectorHeatmapProps) {
  const periods = ["1d", "1w", "1m"];

  const treemapData = sectors.map((s) => ({
    name: s.sector || "Other",
    size: Math.max(1, s.stock_count || 1),
    change_pct: s.change_pct,
  }));

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">Sector Performance</h2>
          <p className="text-xs text-zinc-400 mt-0.5">Color intensity indicates magnitude of gain or loss</p>
        </div>
        <div className="inline-flex items-center rounded-lg bg-zinc-800/80 p-1 border border-zinc-700/50 self-start sm:self-auto">
          {periods.map((period) => (
            <button
              key={period}
              type="button"
              onClick={() => onPeriodChange(period)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${activePeriod === period ? "bg-zinc-700 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"}`}
            >
              {period.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {sectors.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No sector performance data available</div>
      ) : (
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap data={treemapData} dataKey="size" aspectRatio={4 / 3} stroke="#09090b" content={<CustomTreemapCell />} />
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-4 flex items-center justify-center gap-4 text-[11px] text-zinc-400">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-[#ef4444]" /> &lt; -1.5%</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-[#3f3f46]" /> ~0%</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-[#00dc82]" /> &gt; +1.5%</span>
      </div>
    </div>
  );
}
