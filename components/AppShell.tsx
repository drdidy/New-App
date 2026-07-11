"use client";

import Link from "next/link";
import { Settings } from "lucide-react";
import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";
import SpeakButton from "@/components/SpeakButton";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, data } = useStore();

  if (!ready) {
    return (
      <div className="boot">
        <div className="seal">MC</div>
      </div>
    );
  }

  if (!data.onboarded) {
    return <Onboarding />;
  }

  return (
    <div className="shell">
      <header className="masthead">
        <Link href="/" className="masthead-brand" aria-label="Money Coach home">
          <span className="seal">MC</span>
          <span className="masthead-name">Money Coach</span>
        </Link>
        <Link href="/settings" className="btn-icon" aria-label="Settings">
          <Settings size={18} aria-hidden="true" />
        </Link>
      </header>
      {children}
      <SpeakButton />
      <BottomNav />
    </div>
  );
}
