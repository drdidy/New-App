"use client";

import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, data } = useStore();

  // Avoid a flash of the wrong screen before localStorage loads.
  if (!ready) {
    return (
      <div className="app boot">
        <div className="boot-logo">💸</div>
      </div>
    );
  }

  if (!data.onboarded) {
    return (
      <div className="app">
        <Onboarding />
      </div>
    );
  }

  return (
    <>
      <div className="app">{children}</div>
      <BottomNav />
    </>
  );
}
