"use client";

import Link from "next/link";
import { Bell, Settings } from "lucide-react";
import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";
import SpeakButton from "@/components/SpeakButton";

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
    <div className="app-frame vision-shell">
      <header className="topbar vision-mobile-topbar">
        <Link href="/" className="brand-lockup" aria-label="Money Coach home">
          <span className="brand-mark">MC</span>
          <span>
            <strong>Money Coach</strong>
            <small>Daily money clarity</small>
          </span>
        </Link>
        <div className="vision-mobile-actions">
          <button className="topbar-action" aria-label="Notifications">
            <Bell size={18} aria-hidden="true" />
            <span />
          </button>
          <Link href="/settings" className="topbar-action" aria-label="Settings">
            <Settings size={18} aria-hidden="true" />
          </Link>
        </div>
      </header>
      <div className="app">{children}</div>
      <SpeakButton />
      <BottomNav />
    </div>
  );
}
