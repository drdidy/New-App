"use client";

import { useEffect, useRef, useState } from "react";
import { formatMoney } from "@/lib/format";

// Smoothly counts up (or down) to `value` whenever it changes, with an
// ease-out so the balance feels alive when you open the app or log something.
export default function AnimatedNumber({
  value,
  currency = "USD",
  duration = 900,
}: {
  value: number;
  currency?: string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const from = fromRef.current;
    const to = value;
    if (from === to) return;
    const start = performance.now();

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        fromRef.current = to;
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      fromRef.current = to;
    };
  }, [value, duration]);

  return <>{formatMoney(Math.round(display), currency)}</>;
}
