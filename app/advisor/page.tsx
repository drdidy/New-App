"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, Bot, Mic, Send, Sparkles } from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  budgetStatus,
  cashOnHand,
  categoryBreakdown,
  inferDebtKind,
  moneyPlan,
  monthOverMonth,
  netWorth,
  pace,
  safeToSpend,
} from "@/lib/insights";
import { formatMoney } from "@/lib/format";
import { postJson } from "@/lib/clientApi";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const STARTERS = [
  "Budget review",
  "Savings boost",
  "Debt plan",
  "Investing 101",
];

export default function AdvisorPage() {
  const { data, ready } = useStore();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const hasChattedRef = useRef(false);
  const recogRef = useRef<any>(null);
  const finalRef = useRef("");

  useEffect(() => {
    if (!hasChattedRef.current) return;
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  useEffect(() => {
    if (!ready) return;
    if (typeof sessionStorage !== "undefined" && sessionStorage.getItem("mc-checkin") === "1") {
      sessionStorage.removeItem("mc-checkin");
      send("Do my weekly check-in");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  async function sendMessage(text: string) {
    const value = text.trim();
    if (!value || busy) return;
    hasChattedRef.current = true;
    const next = [...msgs, { role: "user" as const, content: value }];
    setMsgs(next);
    setInput("");
    setBusy(true);

    const nameOf = (id?: string) => data.members.find((m) => m.id === id)?.name ?? null;
    const sum = summarize(data);
    const snapshot = {
      household: data.householdName || null,
      members: data.members.map((m) => ({ name: m.name, monthlyIncome: m.monthlyIncome ?? null })),
      ...sum,
      currency: data.currency,
      moneyPlan: moneyPlan(data),
      pace: pace(data, sum.safeToSpend),
      // The real, cash-grounded headline: spendable cash now minus what's due
      // before the next payday. This is what the user actually feels mid-month.
      safeToSpendNow: safeToSpend(data),
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
      topCategories: categoryBreakdown(data).slice(0, 6).map((c) => ({
        category: c.category,
        amount: Math.round(c.amount),
      })),
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
        kind: d.kind ?? inferDebtKind(d),
        balance: d.balance,
        apr: d.apr ?? null,
        minPayment: d.minPayment ?? null,
        dueDate: d.dueDate ?? null,
        paymentsMade: d.payments?.length ?? 0,
        whose: nameOf(d.memberId),
      })),
      recentExpenses: data.transactions.filter((t) => t.type === "expense").slice(0, 24).map((t) => ({
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

    const r = await postJson<{ reply?: string }>("/api/advisor", { messages: next, snapshot });
    setBusy(false);
    if (!r.ok) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: r.error || "Coach couldn’t connect right now. Your local plan is still available." },
      ]);
      return;
    }
    const reply = (r.data?.reply || "").trim();
    setMsgs((m) => [
      ...m,
      { role: "assistant", content: reply || "I’m here — could you say a bit more about what you’d like help with?" },
    ]);
  }

  function send(text: string) {
    void sendMessage(text);
  }

  function toggleVoice() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setVoiceNote("Voice input isn't supported in this browser — try Chrome on Android, or just type. 🙂");
      return;
    }
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    const recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.continuous = false;
    finalRef.current = "";
    recog.onresult = (ev: any) => {
      let t = "";
      for (let i = 0; i < ev.results.length; i++) t += ev.results[i][0].transcript;
      finalRef.current = t;
      setInput(t);
    };
    recog.onerror = (ev: any) => {
      setListening(false);
      if (ev?.error === "not-allowed" || ev?.error === "service-not-allowed") {
        setVoiceNote("Microphone access is blocked. Allow the mic for this site, then try again.");
      } else if (ev?.error === "no-speech") {
        setVoiceNote("I didn't catch that — tap the mic and try again.");
      } else if (ev?.error !== "aborted") {
        setVoiceNote("Voice input had a problem. Typing still works.");
      }
    };
    recog.onend = () => {
      setListening(false);
      const v = finalRef.current.trim();
      finalRef.current = "";
      if (v) send(v);
    };
    recogRef.current = recog;
    setListening(true);
    setVoiceNote("");
    try {
      recog.start();
    } catch {
      setListening(false);
      setVoiceNote("Couldn't start the microphone. Typing still works.");
    }
  }

  if (!ready) return null;

  const firstName = data.members[0]?.name?.split(" ")[0] || "there";
  const sum = summarize(data);
  const sts = safeToSpend(data);
  const debtTotal = data.debts.filter((d) => d.direction === "i_owe").reduce((s, d) => s + d.balance, 0);
  const hasMoneyHistory =
    data.transactions.length > 0 || data.recurringBills.length > 0 || data.goals.length > 0 || debtTotal > 0 || (data.accounts?.length ?? 0) > 0;
  const cur = data.currency;

  return (
    <main className="lx lx-coach">
      <header className="lx-top">
        <div>
          <p className="lx-eyebrow"><Sparkles size={13} /> Built on your real numbers</p>
          <h1 className="lx-h1">Coach</h1>
        </div>
        <span className="lx-coach-avatar"><Bot size={20} /></span>
      </header>

      {hasMoneyHistory && (
        <div className="lx-coach-strip">
          <div>
            <span>Safe to spend</span>
            <b className={sts.safe >= 0 ? "pos" : "neg"}>{formatMoney(sts.safe, cur)}</b>
          </div>
          <div>
            <span>You owe</span>
            <b className="neg">{formatMoney(debtTotal, cur)}</b>
          </div>
          <div>
            <span>Net worth</span>
            <b>{formatMoney(netWorth(data), cur)}</b>
          </div>
        </div>
      )}

      <div className="lx-chat">
        {msgs.length === 0 && (
          <div className="lx-bubble coach">
            {hasMoneyHistory
              ? `Hi ${firstName === "there" ? "there" : firstName} — I can see your latest numbers. Ask me anything, or tap a starter below.`
              : "Welcome in. Add a few transactions, bills, or balances and I'll turn them into a calm, specific plan. Ask me anything to start."}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={"lx-bubble " + (m.role === "user" ? "me" : "coach")}>{m.content}</div>
        ))}
        {busy && <div className="lx-typing"><span /><span /><span /></div>}
        <div ref={endRef} />
      </div>

      {msgs.length === 0 && (
        <div className="lx-chips lx-coach-starters">
          {STARTERS.map((s) => (
            <button key={s} className="lx-chip" onClick={() => send(s)}>{s} <ArrowRight size={12} /></button>
          ))}
        </div>
      )}

      {voiceNote && <p className="lx-voicenote">{voiceNote}</p>}

      <div className="lx-chatbar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(input); }}
          placeholder={listening ? "Listening…" : "Ask your coach anything…"}
        />
        <button aria-label={listening ? "Stop voice input" : "Voice input"} className={"ghost" + (listening ? " live" : "")} onClick={toggleVoice}><Mic size={18} /></button>
        <button aria-label="Send" onClick={() => send(input)} disabled={busy}><Send size={18} /></button>
      </div>
    </main>
  );
}
