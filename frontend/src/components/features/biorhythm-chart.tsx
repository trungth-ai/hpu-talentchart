'use client';

// Biểu đồ nhịp sinh học (Biorhythm) — SVG thuần, không cần thư viện chart.
// 3 đường: Thể chất / Cảm xúc / Trí tuệ, quanh mốc "hôm nay".

import type { BiorhythmPoint } from '@/lib/types';

const W = 600;
const H = 180;
const PAD = 24;

const LINES = [
  { key: 'physical', label: 'Thể chất', color: '#2563eb' },
  { key: 'emotional', label: 'Cảm xúc', color: '#16a34a' },
  { key: 'intellectual', label: 'Trí tuệ', color: '#d97706' },
] as const;

export function BiorhythmChart({
  series,
  today,
}: {
  series: BiorhythmPoint[];
  today: { physical: number; emotional: number; intellectual: number };
}) {
  if (!series.length) return null;
  const n = series.length;
  const x = (i: number) => PAD + (i / (n - 1)) * (W - 2 * PAD);
  const y = (v: number) => H / 2 - (v / 100) * (H / 2 - PAD);
  const zeroIdx = series.findIndex((s) => s.offset === 0);

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-3 text-xs text-gray-600">
        {LINES.map((l) => (
          <span key={l.key} className="inline-flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded" style={{ background: l.color }} />
            {l.label}:{' '}
            <b>
              {today[l.key] > 0 ? '+' : ''}
              {today[l.key]}%
            </b>
          </span>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Biểu đồ nhịp sinh học">
        {/* trục 0% */}
        <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="#e5e7eb" strokeWidth={1} />
        {/* mốc hôm nay */}
        {zeroIdx >= 0 && (
          <line
            x1={x(zeroIdx)}
            y1={PAD}
            x2={x(zeroIdx)}
            y2={H - PAD}
            stroke="#9ca3af"
            strokeDasharray="4 3"
            strokeWidth={1}
          />
        )}
        {LINES.map((l) => (
          <polyline
            key={l.key}
            fill="none"
            stroke={l.color}
            strokeWidth={2}
            points={series.map((s, i) => `${x(i)},${y(s[l.key])}`).join(' ')}
          />
        ))}
        {zeroIdx >= 0 &&
          LINES.map((l) => (
            <circle key={l.key} cx={x(zeroIdx)} cy={y(series[zeroIdx][l.key])} r={3} fill={l.color} />
          ))}
      </svg>
      <div className="flex justify-between text-[10px] text-gray-400">
        <span>{series[0]?.date?.slice(5)}</span>
        <span>Hôm nay</span>
        <span>{series[n - 1]?.date?.slice(5)}</span>
      </div>
    </div>
  );
}
