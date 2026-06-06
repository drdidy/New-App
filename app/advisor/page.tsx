"use client";

import { useEffect, useRef, useState } from "react";
import { useStore, summarize } from "@/lib/store";
import {
  categoryBreakdown,
  monthOverMonth,
  budgetStatus,
  billsThisMonth,
  moneyPlan,
  pace,
  netWorth,
  cashOnHand,
} from "@/lib/insights";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const STARTERS = [
  "Build me a monthly budget plan",
  "Do my weekly check-in",
  "Compare debt payoff strategies",
  "Find grocery line-item patterns",
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

  // If we arrived here from the weekly check-in banner, kick it off.
  useEffect(() => {
    if (!ready) return;
    if (typeof sessionStorage !== "undefined" && sessionStorage.getItem("mc-checkin") === "1") {
      sessionStorage.removeItem("mc-checkin");
      send("Do my weekly check-in");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  async function send(text: string) {
    const value = text.trim();
    if (!value || busy) return;
    const next = [...msgs, { role: "user" as const, content: value }];
    setMsgs(next);
    setInput("");
    setBusy(true);

    const nameOf = (id?: string) =>
      data.members.find((m) => m.id === id)?.name ?? null;

    const sum = summarize(data);
    const snapshot = {
      household: data.householdName || null,
      members: data.members.map((m) => ({
        name: m.name,
        monthlyIncome: m.monthlyIncome ?? null,
      })),
      ...sum,
      currency: data.currency,
      moneyPlan: moneyPlan(data),
      pace: pace(data, sum.safeToSpend),
      netWorth: netWorth(data),
      cashOnHand: cashOnHand(data),
      goals: (data.goals || []).map((g) => ({
        name: g.name,
        target: g.target,
        saved: g.saved,
        monthlyContribution: g.monthlyContribution ?? null,
      })),
      budgets: budgetStatus(data).map((b) => ({
        category: b.category,
        spent: Math.round(b.spent),
        limit: b.limit,
        over: b.over,
      })),
      topCategories: categoryBreakdown(data)
        .slice(0, 6)
        .map((c) => ({ category: c.category, amount: Math.round(c.amount) })),
      monthOverMonth: monthOverMonth(data),
      recurringBills: billsThisMonth(data).map((b) => ({
        name: b.bill.name,
        amount: b.bill.amount,
        category: b.bill.category,
        dueDay: b.dueDay,
        paid: b.paid,
        whose: nameOf(b.bill.memberId),
      })),
      debts: data.debts.map((d) => ({
        party: d.party,
        direction: d.direction,
        balance: d.balance,
        apr: d.apr ?? null,
        minPayment: d.minPayment ?? null,
        dueDate: d.dueDate ?? null,
        whose: nameOf(d.memberId),
      })),
      recentExpenses: data.transactions
        .filter((t) => t.type === "expense")
        .slice(0, 24)
        .map((t) => ({
          amount: t.amount,
          category: t.category,
          date: t.date,
          who: nameOf(t.memberId),
          lineItems: t.lineItems?.slice(0, 20).map((item) => ({
            name: item.name,
            amount: item.amount,
            category: item.category,
          })),
        })),
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
        Judgment-free advice based on your real numbers. Coach sends a compact
        snapshot to Claude through the server; your API key stays private.
      </p>

      {msgs.length === 0 && (
        <>
          <div className="bubble coach" style={{ maxWidth: "100%" }}>
            Hi — I&apos;m Coach. I can see {data.members.length > 1 ? "your household's" : "your"} budget and
            debts, and I&apos;m here to help you get on top of them one small step
            at a time. What&apos;s weighing on you?
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
