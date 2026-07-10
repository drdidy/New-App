"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { formatMoney } from "@/lib/format";

// GSAP-eased count-up to `value`, with a subtle scale "pop" whenever it changes,
// so the balance feels alive when you open the app or log something.
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
  const elRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduce || fromRef.current === value) {
      setDisplay(value);
      fromRef.current = value;
      return;
    }

    const obj = { v: fromRef.current };
    const tween = gsap.to(obj, {
      v: value,
      duration: duration / 1000,
      ease: "power2.out",
      onUpdate: () => {
        setDisplay(obj.v);
        // Track what's actually on screen, so an interrupted animation resumes
        // from the displayed number instead of jumping to the old target.
        fromRef.current = obj.v;
      },
      onComplete: () => {
        fromRef.current = value;
      },
    });
    if (elRef.current) {
      gsap.fromTo(
        elRef.current,
        { scale: 0.97 },
        { scale: 1, duration: 0.5, ease: "back.out(2)" },
      );
    }
    return () => {
      tween.kill();
    };
  }, [value, duration]);

  return (
    <span ref={elRef} style={{ display: "inline-block" }}>
      {formatMoney(Math.round(display), currency)}
    </span>
  );
}
