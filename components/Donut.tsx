"use client";

import { useEffect, useState } from "react";

export interface DonutSlice {
  label: string;
  value: number;
  color: string;
}

// An animated donut chart. Slices grow in on mount. `centerTop`/`centerSub`
// render in the hole.
export default function Donut({
  slices,
  size = 168,
  stroke = 22,
  centerTop,
  centerSub,
}: {
  slices: DonutSlice[];
  size?: number;
  stroke?: number;
  centerTop?: React.ReactNode;
  centerSub?: React.ReactNode;
}) {
  const [grow, setGrow] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setGrow(1));
    return () => cancelAnimationFrame(id);
  }, [slices]);

  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  let acc = 0;

  return (
    <div className="donut" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.07)"
          strokeWidth={stroke}
        />
        {slices.map((s, i) => {
          const frac = (s.value / total) * grow;
          const len = frac * c;
          const dash = `${len} ${c - len}`;
          const offset = -acc * c;
          acc += s.value / total;
          return (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeDasharray={dash}
              strokeDashoffset={offset}
              strokeLinecap="butt"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              style={{ transition: "stroke-dasharray 0.9s cubic-bezier(0.22,1,0.36,1)" }}
            />
          );
        })}
      </svg>
      {(centerTop != null || centerSub != null) && (
        <div className="donut-center">
          {centerTop != null && <div className="donut-top">{centerTop}</div>}
          {centerSub != null && <div className="donut-sub">{centerSub}</div>}
        </div>
      )}
    </div>
  );
}
