"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";

const WEEK = 7 * 24 * 60 * 60 * 1000;

// Shows a gentle weekly check-in prompt on Home once it's been ~a week. If the
// user enabled reminders and granted notification permission, also fires a
// best-effort notification when the app opens and a check-in is due. (True
// background push needs a push server; this nudges on open.)
export default function CheckInBanner() {
  const { data, ready, markCheckIn } = useStore();
  const router = useRouter();

  const due =
    ready &&
    data.transactions.length > 0 &&
    (!data.lastCheckIn || Date.now() - data.lastCheckIn > WEEK);

  useEffect(() => {
    if (!due || !data.remindersEnabled) return;
    if (typeof Notification === "undefined" || Notification.permission !== "granted") return;
    if (sessionStorage.getItem("mc-notified")) return;
    sessionStorage.setItem("mc-notified", "1");
    try {
      new Notification("Money Coach", {
        body: "It's time for your weekly money check-in 💪",
        icon: "/icon.svg",
      });
    } catch {
      /* best effort */
    }
  }, [due, data.remindersEnabled]);

  if (!due) return null;

  function start() {
    markCheckIn();
    sessionStorage.setItem("mc-checkin", "1");
    router.push("/coach");
  }

  return (
    <div className="checkin reveal">
      <span className="ci-emoji">👋</span>
      <div className="ci-text">
        <div className="ci-title">Ready for your weekly check-in?</div>
        <div className="ci-sub">A 1-minute review with one thing to focus on this week.</div>
      </div>
      <button className="bill-pay" onClick={start}>Start</button>
      <button className="ci-x" onClick={() => markCheckIn()} aria-label="Dismiss">×</button>
    </div>
  );
}
