"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Settings } from "lucide-react";
import { useStore } from "@/lib/store";
import BottomNav from "@/components/BottomNav";
import Onboarding from "@/components/Onboarding";
import SpeakButton from "@/components/SpeakButton";
import { billsThisMonth } from "@/lib/insights";
import { isoWeekId } from "@/lib/format";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { ready, data } = useStore();

  // Ask the browser to protect our storage from eviction — the entire ledger
  // lives in localStorage, so this is the difference between "app data" and
  // "disposable cache" to the OS. Safe no-op where unsupported.
  useEffect(() => {
    if (!ready || !data.onboarded) return;
    navigator.storage?.persist?.().catch(() => {});
  }, [ready, data.onboarded]);

  // App-icon badge: bills due today still unpaid, plus an unread Weekly
  // Edition. Cleared the moment there is nothing that needs the user.
  useEffect(() => {
    if (!ready || !data.onboarded) return;
    const nav = navigator as Navigator & {
      setAppBadge?: (n: number) => Promise<void>;
      clearAppBadge?: () => Promise<void>;
    };
    if (!nav.setAppBadge) return;
    let n = billsThisMonth(data).filter((b) => !b.paid && b.daysAway === 0).length;
    try { if (localStorage.getItem("mc-week-read") !== isoWeekId()) n += 1; } catch {}
    if (n > 0) nav.setAppBadge(n).catch(() => {});
    else nav.clearAppBadge?.().catch(() => {});
  }, [ready, data]);

  // Weekly-edition reminder: a periodic background sync (where supported)
  // that lets the service worker announce each new issue. Registered only
  // when the user has reminders on AND has granted notifications.
  useEffect(() => {
    if (!ready || !data.onboarded) return;
    navigator.serviceWorker?.ready.then((reg) => {
      const sync = (reg as unknown as { periodicSync?: { register: (tag: string, opts: { minInterval: number }) => Promise<void>; unregister: (tag: string) => Promise<void> } }).periodicSync;
      if (!sync) return;
      const wanted = Boolean(data.remindersEnabled) && typeof Notification !== "undefined" && Notification.permission === "granted";
      (wanted
        ? sync.register("weekly-edition", { minInterval: 12 * 60 * 60 * 1000 })
        : sync.unregister("weekly-edition")
      ).catch(() => {});
    }).catch(() => {});
  }, [ready, data.onboarded, data.remindersEnabled]);

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
