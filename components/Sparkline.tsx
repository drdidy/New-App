"use client";

// A compact area+line chart for a series of values (e.g. net worth over months).
export default function Sparkline({
  values,
  labels,
  color = "#2e8b72",
  height = 90,
}: {
  values: number[];
  labels?: string[];
  color?: string;
  height?: number;
}) {
  const w = 300;
  const h = height;
  const pad = 8;
  if (values.length === 0) return null;

  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;
  const n = values.length;
  const x = (i: number) => (n === 1 ? w / 2 : pad + (i * (w - pad * 2)) / (n - 1));
  const y = (v: number) => h - pad - ((v - min) / range) * (h - pad * 2);

  const pts = values.map((v, i) => `${x(i)},${y(v)}`);
  const line = pts.map((p, i) => (i === 0 ? `M${p}` : `L${p}`)).join(" ");
  const area = `${line} L${x(n - 1)},${h - pad} L${x(0)},${h - pad} Z`;

  return (
    <div className="spark">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" width="100%" height={h}>
        <defs>
          <linearGradient id="sparkfill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.28" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#sparkfill)" />
        <path d={line} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {values.map((v, i) => (
          <circle key={i} cx={x(i)} cy={y(v)} r={n > 12 ? 0 : 3} fill={color} />
        ))}
      </svg>
      {labels && (
        <div className="spark-labels">
          {labels.map((l, i) => (
            <span key={i}>{l}</span>
          ))}
        </div>
      )}
    </div>
  );
}
