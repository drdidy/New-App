"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  CircleDollarSign,
  ClipboardList,
  CreditCard,
  ReceiptText,
  ShieldAlert,
  TrendingDown,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import { billsThisMonth, pace, quickInsights } from "@/lib/insights";
import { formatMoney, friendlyDate } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";
import QuickCapture from "@/components/QuickCapture";
import MemberPicker from "@/components/MemberPicker";
import Avatar from "@/components/Avatar";
import CheckInBanner from "@/components/CheckInBanner";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function statusFor(safeToSpend: number, billsDue: number, debtDue: number) {
  if (safeToSpend < 0) {
    return {
      label: "Recovery needed",
      tone: "danger",
      Icon: ShieldAlert,
      text: "Your plan is over pressure. Coach can help find the smallest correction.",
    };
  }
  if (billsDue + debtDue > safeToSpend * 0.7 && safeToSpend > 0) {
    return {
      label: "Watch commitments",
      tone: "warn",
      Icon: AlertTriangle,
      text: "Upcoming bills and debt minimums take most of the room left.",
    };
  }
  return {
    label: "On track",
    tone: "good",
    Icon: CheckCircle2,
    text: "You have spending room after logged expenses, bills, and minimum payments.",
  };
}

export default function TodayPage() {
  const { data, ready, deleteTransaction, markBillPaid, member } = useStore();
  const [view, setView] = useState<string | undefined>(undefined);
  if (!ready) return null;

  const multi = data.members.length > 1;
  const summary = summarize(data, view);
  const upcomingBills = billsThisMonth(data, view).filter((b) => !b.paid);
  const totalBillsDue = upcomingBills.reduce((sum, b) => sum + b.bill.amount, 0);
  const debtMinimums = data.debts
    .filter((d) => d.direction === "i_owe" && (!view || d.memberId === view))
    .reduce((sum, d) => sum + (d.minPayment || 0), 0);
  const status = statusFor(summary.safeToSpend, totalBillsDue, debtMinimums);
  const dailyPace = pace(data, summary.safeToSpend);
  const insights = quickInsights(data, data.currency).slice(0, 3);
  const recent = data.transactions
    .filter((t) => !view || t.memberId === view)
    .slice(0, 8);
  const firstName = data.members[0]?.name?.split(" ")[0];
  const nextBill = upcomingBills[0];
  const debtTarget = data.debts
    .filter((d) => d.direction === "i_owe" && d.balance > 0)
    .sort((a, b) => (b.apr || 0) - (a.apr || 0))[0];

  const nextAction = summary.safeToSpend < 0
    ? {
        href: "/advisor",
        title: "Ask Coach for a recovery plan",
        body: "Get one specific adjustment to bring this month back under control.",
        Icon: TrendingDown,
      }
    : nextBill
    ? {
        href: "/bills",
        title: `Confirm ${nextBill.bill.name}`,
        body: `${formatMoney(nextBill.bill.amount, data.currency)} is still committed this month.`,
        Icon: CalendarClock,
      }
    : debtTarget
    ? {
        href: "/debts",
        title: `Review ${debtTarget.party}`,
        body: "Compare snowball, avalanche, and hybrid payoff routes.",
        Icon: CreditCard,
      }
    : {
        href: "/plan",
        title: "Finish your first monthly plan",
        body: "Add bills, budgets, and a starter goal so safe-to-spend becomes accurate.",
        Icon: ClipboardList,
      };

  return (
    <main className="today-page">
      <header className="today-hero">
        <div>
          <p className="eyebrow">{greeting()}{firstName ? `, ${firstName}` : ""}</p>
          <h1 className="h-title">
            {data.householdName || "Today"}
          </h1>
          <p className="h-sub">
            A plain-English view of what is safe, what needs attention, and what to do next.
          </p>
        </div>
        <div className="today-people">
          {data.members.map((m) => (
            <Avatar key={m.id} member={m} size={36} />
          ))}
        </div>
      </header>

      <CheckInBanner />

      {multi && (
        <section className="today-filter">
          <MemberPicker
            members={data.members}
            value={view}
            onChange={setView}
            allLabel="Everyone"
            size="sm"
          />
        </section>
      )}

      <section className="today-grid">
        <div className="card money-status">
          <div className="status-row">
            <span className={`status-pill ${status.tone}`}>
              <status.Icon size={15} aria-hidden="true" />
              {status.label}
            </span>
            <span className="muted">Safe to spend</span>
          </div>
          <div className="money-xl">
            <AnimatedNumber value={summary.safeToSpend} currency={data.currency} />
          </div>
          <p>{status.text}</p>
          {summary.safeToSpend >= 0 && (
            <div className="daily-pace">
              <CircleDollarSign size={18} aria-hidden="true" />
              <span>
                {formatMoney(dailyPace.dailyAllowance, data.currency)} per day keeps this period on track.
              </span>
            </div>
          )}
        </div>

        <Link href={nextAction.href} className="card next-action">
          <div className="action-icon">
            <nextAction.Icon size={22} aria-hidden="true" />
          </div>
          <div>
            <p className="eyebrow">Next best move</p>
            <h2>{nextAction.title}</h2>
            <p>{nextAction.body}</p>
          </div>
          <ArrowRight className="action-arrow" size={20} aria-hidden="true" />
        </Link>

        <div className="metric-strip">
          <div className="card metric-card">
            <span>Income</span>
            <strong className="pos">{formatMoney(summary.income, data.currency)}</strong>
          </div>
          <div className="card metric-card">
            <span>Spent</span>
            <strong className="neg">{formatMoney(summary.expenses, data.currency)}</strong>
          </div>
          <div className="card metric-card">
            <span>Bills left</span>
            <strong>{formatMoney(totalBillsDue, data.currency)}</strong>
          </div>
          <div className="card metric-card">
            <span>Debt owed</span>
            <strong className="neg">{formatMoney(summary.totalIOwe, data.currency)}</strong>
          </div>
        </div>

        <section className="capture-panel">
          <div className="section-title">
            <div>
              <p className="eyebrow">Quick capture</p>
              <h2>Log money before it gets fuzzy</h2>
            </div>
          </div>
          <QuickCapture />
        </section>

        <aside className="attention-panel">
          <div className="card">
            <div className="card-h">Needs attention</div>
            {insights.length === 0 && upcomingBills.length === 0 && !debtTarget ? (
              <div className="empty">
                Add a few transactions, bills, or debts and this panel will become your daily checklist.
              </div>
            ) : (
              <div className="attention-list">
                {upcomingBills.slice(0, 3).map((b) => (
                  <div className="attention-item" key={b.bill.id}>
                    <CalendarClock size={18} aria-hidden="true" />
                    <div>
                      <strong>{b.bill.name}</strong>
                      <span>{formatMoney(b.bill.amount, data.currency)} due day {b.dueDay}</span>
                    </div>
                    <button className="bill-pay" onClick={() => markBillPaid(b.bill.id)}>
                      Paid
                    </button>
                  </div>
                ))}
                {debtTarget && (
                  <Link href="/debts" className="attention-item">
                    <CreditCard size={18} aria-hidden="true" />
                    <div>
                      <strong>{debtTarget.party}</strong>
                      <span>{formatMoney(debtTarget.balance, data.currency)} balance</span>
                    </div>
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                )}
                {insights.map((text) => (
                  <div className="attention-item" key={text}>
                    <AlertTriangle size={18} aria-hidden="true" />
                    <div>
                      <strong>Pattern found</strong>
                      <span>{text}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        <section className="card recent-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Ledger</p>
              <h2>Recent activity</h2>
            </div>
            <Link href="/insights">Spending details</Link>
          </div>
          {recent.length === 0 ? (
            <div className="empty">
              Start with one sentence, like <strong>spent 12 on lunch</strong>.
            </div>
          ) : (
            recent.map((t) => {
              const owner = member(t.memberId);
              return (
                <div className="ledger-row" key={t.id}>
                  <div className="ledger-icon">
                    <ReceiptText size={18} aria-hidden="true" />
                  </div>
                  <div className="ledger-main">
                    <strong>{t.description || t.category}</strong>
                    <span>
                      {t.category} · {friendlyDate(t.date)}
                      {multi && owner ? ` · ${owner.name.split(" ")[0]}` : ""}
                    </span>
                    {t.lineItems?.length ? (
                      <span className="receipt-note">{t.lineItems.length} receipt line items captured</span>
                    ) : null}
                  </div>
                  <div className={t.type === "income" ? "ledger-amount pos" : "ledger-amount neg"}>
                    {t.type === "income" ? "+" : "-"}
                    {formatMoney(t.amount, data.currency)}
                  </div>
                  <button
                    className="x"
                    onClick={() => deleteTransaction(t.id)}
                    aria-label="Delete transaction"
                  >
                    ×
                  </button>
                </div>
              );
            })
          )}
        </section>
      </section>
    </main>
  );
}
