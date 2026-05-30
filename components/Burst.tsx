"use client";

// A tiny, dependency-free confetti burst. Render it (keyed) when you want a
// celebratory pop — e.g. right after the user logs an expense. It cleans up
// after the animation, so just bump the `fire` key to retrigger.
const COLORS = ["#f3c14e", "#5fe0a6", "#ff8d6b", "#b08cff", "#7fb6e8"];
const PIECES = 14;

export default function Burst() {
  return (
    <div className="burst" aria-hidden="true">
      {Array.from({ length: PIECES }).map((_, i) => {
        const angle = (i / PIECES) * Math.PI * 2;
        const dist = 46 + Math.random() * 34;
        const tx = Math.cos(angle) * dist;
        const ty = Math.sin(angle) * dist - 10;
        return (
          <i
            key={i}
            style={{
              background: COLORS[i % COLORS.length],
              // @ts-expect-error -- CSS custom props
              "--tx": `${tx}px`,
              "--ty": `${ty}px`,
              animationDelay: `${Math.random() * 0.05}s`,
            }}
          />
        );
      })}
    </div>
  );
}
