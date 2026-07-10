"use client";

// Re-mounts on every route change, so each screen enters with the same
// choreographed motion — one cohesive transition system app-wide.
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="route-in">{children}</div>;
}
