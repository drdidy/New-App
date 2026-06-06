"use client";

import Link from "next/link";
import { Settings } from "lucide-react";
import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, data } = useStore();

  if (!ready) {
    return (
      <div className="app boot">
        <div className="boot-logo">MC</div>
      </div>
    );
  }

  if (!data.onboarded) {
    return (
      <div className="app-frame onboarding-frame">
        <div className="app">
          <Onboarding />
        </div>
      </div>
    );
  }

  return (
    <div className="app-frame">
      <header className="topbar">
        <Link href="/" className="brand-lockup" aria-label="Money Coach home">
          <span className="brand-mark">MC</span>
          <span>
            <strong>Money Coach</strong>
            <small>Household finance cockpit</small>
          </span>
        </Link>
        <Link href="/settings" className="topbar-action" aria-label="Settings">
          <Settings size={18} aria-hidden="true" />
        </Link>
      </header>
      <div className="app">{children}</div>
      <BottomNav />
    </div>
  );
}
