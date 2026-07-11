"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowRight, Mic, Moon, Plus, Send, Sparkles, X } from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  affordCheck,
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
import { success } from "@/lib/haptics";
import { postJson } from "@/lib/clientApi";
import AnimatedNumber from "@/components/AnimatedNumber";

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
  const { data, ready, addWish, decideWish, deleteWish } = useStore();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState("");
  const [affordQ, setAffordQ] = useState("");
  const [wishName, setWishName] = useState("");
  const [wishAmt, setWishAmt] = useState("");
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
  const sts = safeToSpend(data);
  const debtTotal = data.debts.filter((d) => d.direction === "i_owe").reduce((s, d) => s + d.balance, 0);
  const hasMoneyHistory =
    data.transactions.length > 0 || data.recurringBills.length > 0 || data.goals.length > 0 || debtTotal > 0 || (data.accounts?.length ?? 0) > 0;
  const cur = data.currency;
  const nw = netWorth(data);

  const COOL_DAYS = 3;
  const pendingWishes = (data.wishlist || []).filter((w) => !w.outcome).sort((a, b) => a.createdAt - b.createdAt);
  const savedByWaiting = (data.wishlist || []).filter((w) => w.outcome === "skipped").reduce((s, w) => s + w.amount, 0);
  const afford = affordCheck(data, parseFloat(affordQ) || 0);

  function addW() {
    const a = parseFloat(wishAmt);
    if (!wishName.trim() || !(a > 0)) return;
    addWish(wishName.trim(), a); success(); setWishName(""); setWishAmt("");
  }

  return (
    <main className="pg">
      <div className="pg-head">
        <p className="pg-date">Built on your real numbers</p>
      </div>
      <h1 className="pg-title">Coach</h1>
      <div className="pg-rule" />

      {hasMoneyHistory && (
        <div className="ticker">
          <Link href="/" className="ticker-cell">
            <span className="tk-l">Safe to spend</span>
            <span className={"tk-v" + (sts.safe >= 0 ? " pos" : " neg")}><AnimatedNumber value={sts.safe} currency={cur} /></span>
          </Link>
          <Link href="/debt" className="ticker-cell">
            <span className="tk-l">You owe</span>
            <span className="tk-v neg"><AnimatedNumber value={debtTotal} currency={cur} /></span>
          </Link>
          <Link href="/spending" className="ticker-cell">
            <span className="tk-l">Net worth</span>
            <span className={"tk-v" + (nw >= 0 ? " pos" : " mut")}><AnimatedNumber value={nw} currency={cur} /></span>
          </Link>
        </div>
      )}

      {/* CAN I AFFORD IT — a straight answer before you spend */}
      <div className="plate">
        <div className="plate-title"><Sparkles /> Can I afford it?</div>
        <div className="inline-form" style={{ marginTop: 12 }}>
          <input
            className="input"
            type="number"
            inputMode="decimal"
            placeholder="Price — e.g. 120"
            value={affordQ}
            onChange={(e) => setAffordQ(e.target.value)}
          />
        </div>
        {afford ? (
          <div className={"verdict " + afford.verdict}>
            <strong>{afford.headline}</strong>
            <span>{afford.detail}</span>
          </div>
        ) : (
          <p className="hint">Type a price and I’ll tell you straight — grounded in your real cash, not vibes.</p>
        )}
      </div>

      {/* SLEEP ON IT */}
      <div className="plate">
        <div className="plate-title">
          <Moon /> Sleep on it
          {savedByWaiting > 0 && <span style={{ marginLeft: "auto", color: "var(--pos)", fontSize: 11.5, letterSpacing: 0, textTransform: "none", fontWeight: 700 }}>{formatMoney(savedByWaiting, cur)} saved by waiting</span>}
        </div>
        <div className="inline-form" style={{ marginTop: 12 }}>
          <input className="input" placeholder="Something you want…" value={wishName} onChange={(e) => setWishName(e.target.value)} />
          <input className="input" style={{ maxWidth: 90, flex: "0 1 90px" }} type="number" inputMode="decimal" placeholder="$" value={wishAmt} onChange={(e) => setWishAmt(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addW()} />
          <button className="btn sm" onClick={addW} disabled={!wishName.trim() || !(parseFloat(wishAmt) > 0)} aria-label="Add to wishlist"><Plus size={15} /></button>
        </div>
        {pendingWishes.length > 0 ? (
          <div style={{ marginTop: 4 }}>
            {pendingWishes.map((w) => {
              const days = Math.floor((Date.now() - w.createdAt) / 86400000);
              const left = Math.max(0, COOL_DAYS - days);
              const readyToDecide = left <= 0;
              const v = readyToDecide ? affordCheck(data, w.amount) : null;
              return (
                <div className="row" key={w.id} style={{ flexWrap: "wrap" }}>
                  <span className="row-ic">{readyToDecide ? "✨" : "💤"}</span>
                  <div className="row-meta">
                    <div className="row-t">{w.name}</div>
                    <div className={"row-s" + (v ? (v.verdict === "yes" ? " pos" : v.verdict === "wait" ? " neg" : "") : "")}>
                      {readyToDecide ? (v ? v.headline : "Ready to decide") : `${left} day${left === 1 ? "" : "s"} to think it over`}
                    </div>
                  </div>
                  <div className="row-amt">{formatMoney(w.amount, cur)}</div>
                  {/* Always removable — "changed my mind" shouldn't pollute the saved-by-waiting stat */}
                  <button className="btn-icon danger" onClick={() => deleteWish(w.id)} aria-label="Remove"><X size={14} /></button>
                  {readyToDecide && (
                    <div style={{ flexBasis: "100%", display: "flex", gap: 8, justifyContent: "flex-end" }}>
                      <button className="btn-ghost sm" onClick={() => { decideWish(w.id, "skipped"); success(); }}>Skip</button>
                      <button className="btn sm" onClick={() => { decideWish(w.id, "bought"); success(); }}>Buy</button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="hint">Tempted by something? Add it here. I’ll hold it for {COOL_DAYS} days — most urges fade, and you’ll see if you can truly afford it then.</p>
        )}
      </div>

      {/* CORRESPONDENCE */}
      <section className="sec">
        <div className="sec-head"><h2>Ask your coach</h2></div>
        <div className="chat">
          {msgs.length === 0 && (
            <>
              <div className="bubble coach">
                {hasMoneyHistory
                  ? `Hi ${firstName === "there" ? "there" : firstName} — I can see your latest numbers. Ask me anything, or tap a starter below.`
                  : "Welcome in. Add a few transactions, bills, or balances and I'll turn them into a calm, specific plan. Ask me anything to start."}
              </div>
              <div className="chips">
                {STARTERS.map((s) => (
                  <button key={s} className="chip" onClick={() => send(s)}>{s} <ArrowRight size={12} style={{ display: "inline", verticalAlign: "-2px" }} /></button>
                ))}
              </div>
            </>
          )}
          {msgs.map((m, i) => (
            <div key={i} className={"bubble " + (m.role === "user" ? "me" : "coach")}>{m.content}</div>
          ))}
          {busy && <div className="typing"><span /><span /><span /></div>}
          <div ref={endRef} />
        </div>

        {voiceNote && <p className="voicenote">{voiceNote}</p>}

        <div className="chatbar">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(input); }}
            placeholder={listening ? "Listening…" : "Ask your coach anything…"}
          />
          <button aria-label={listening ? "Stop voice input" : "Voice input"} className={"mic" + (listening ? " live" : "")} onClick={toggleVoice}><Mic size={18} /></button>
          <button aria-label="Send" className="send" onClick={() => send(input)} disabled={busy}><Send size={18} /></button>
        </div>
      </section>
    </main>
  );
}
