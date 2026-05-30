"use client";

import { useEffect, useRef, useState } from "react";
import { useStore, summarize } from "@/lib/store";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const STARTERS = [
  "Make me a plan to pay off my debts",
  "Where am I overspending?",
  "How much can I safely spend this week?",
  "Who should I pay back first?",
];

export default function AdvisorPage() {
  const { data, ready } = useStore();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  async function send(text: string) {
    const value = text.trim();
    if (!value || busy) return;
    const next = [...msgs, { role: "user" as const, content: value }];
    setMsgs(next);
    setInput("");
    setBusy(true);

    const snapshot = {
      ...summarize(data),
      currency: data.currency,
      debts: data.debts.map((d) => ({
        party: d.party,
        direction: d.direction,
        balance: d.balance,
        apr: d.apr ?? null,
        minPayment: d.minPayment ?? null,
        dueDate: d.dueDate ?? null,
      })),
      recentExpenses: data.transactions
        .filter((t) => t.type === "expense")
        .slice(0, 20)
        .map((t) => ({ amount: t.amount, category: t.category, date: t.date })),
    };

    try {
      const res = await fetch("/api/advisor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next, snapshot }),
      });
      const dataR = await res.json();
      if (!res.ok) throw new Error(dataR.error || "Coach is unavailable.");
      setMsgs((m) => [...m, { role: "assistant", content: dataR.reply }]);
    } catch (e: any) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: "⚠️ " + (e.message || "Something went wrong.") },
      ]);
    } finally {
      setBusy(false);
    }
  }

  if (!ready) return null;

  return (
    <main>
      <h1 className="h-title">Your Money Coach</h1>
      <p className="h-sub">
        Private, judgment-free advice based on your real numbers.
      </p>

      {msgs.length === 0 && (
        <>
          <div className="bubble coach" style={{ maxWidth: "100%" }}>
            Hi — I&apos;m Coach. I can see your budget and debts, and I&apos;m here
            to help you get on top of them one small step at a time. What&apos;s
            weighing on you?
          </div>
          <div className="suggest" style={{ marginTop: 12 }}>
            {STARTERS.map((s) => (
              <button key={s} onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
        </>
      )}

      <div className="chat">
        {msgs.map((m, i) => (
          <div key={i} className={"bubble " + (m.role === "user" ? "me" : "coach")}>
            {m.content}
          </div>
        ))}
        {busy && (
          <div className="typing" aria-label="Coach is thinking">
            <span />
            <span />
            <span />
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") send(input);
          }}
          placeholder="Ask Coach anything about your money…"
        />
        <button
          className="btn btn-primary"
          onClick={() => send(input)}
          disabled={busy}
        >
          Send
        </button>
      </div>
    </main>
  );
}
