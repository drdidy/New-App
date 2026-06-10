"use client";

import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";
import WebGLBackground from "@/components/WebGLBackground";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, data } = useStore();

  // Avoid a flash of the wrong screen before localStorage loads.
  if (!ready) {
    return (
      <div className="app boot">
        <WebGLBackground />
        <div className="boot-logo">💸</div>
      </div>
    );
  }

  if (!data.onboarded) {
    return (
      <div className="app">
        <WebGLBackground />
        <Onboarding />
      </div>
    );
  }

  return (
    <>
      <WebGLBackground />
      <div className="app">{children}</div>
      <BottomNav />
    </>
  );
}
