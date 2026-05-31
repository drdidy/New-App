"use client";

import { useState } from "react";
import { useStore, summarize } from "@/lib/store";
import {
  categoryBreakdown,
  budgetStatus,
  memberSplit,
  monthOverMonth,
  netWorth,
  cashOnHand,
  monthlyTotals,
} from "@/lib/insights";
import { formatMoney, formatMoneyShort, monthLabel, monthKey, MEMBER_COLORS } from "@/lib/format";
import Donut from "@/components/Donut";
import Sparkline from "@/components/Sparkline";
import Avatar from "@/components/Avatar";

const ACCOUNT_EMOJI: Record<string, string> = {
  checking: "🏦",
  savings: "🐷",
  cash: "💵",
  investment: "📈",
  other: "💼",
};

const CHART_COLORS = [
  "#c2663f",
  "#2e8b72",
  "#7c6ba8",
  "#5e7fa6",
  "#bc5446",
  "#a8743f",
  "#6e8c5a",
  "#9c6b8e",
];

export default function InsightsPage() {
  const { data, ready, member, addAccount, updateAccount, deleteAccount } = useStore();
  const [acctOpen, setAcctOpen] = useState(false);
  const [aName, setAName] = useState("");
  const [aType, setAType] = useState<"checking" | "savings" | "cash" | "investment" | "other">("checking");
  const [aBalance, setABalance] = useState("");
  if (!ready) return null;

  const s = summarize(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);
  const splits = memberSplit(data).filter((x) => x.expenses > 0);
  const mom = monthOverMonth(data);
  const hasData = data.transactions.length > 0;

  const nw = netWorth(data);
  const cash = cashOnHand(data);
  const trend = monthlyTotals(data, 6);
  const nwHist = (data.netWorthHistory || []).slice(-6);
  const maxFlow = Math.max(1, ...trend.map((m) => Math.max(m.income, m.expense)));

  function saveAccount() {
    const bal = parseFloat(aBalance);
    if (!aName.trim() || isNaN(bal)) return;
    addAccount({
      name: aName.trim(),
      type: aType,
      balance: bal,
      emoji: ACCOUNT_EMOJI[aType],
      color: MEMBER_COLORS[(data.accounts?.length || 0) % MEMBER_COLORS.length],
    });
    setAName(""); setABalance(""); setAcctOpen(false);
  }

  const slices = cats.slice(0, 7).map((c, i) => ({
    label: c.category,
    value: c.amount,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <main>
      <h1 className="h-title">Insights</h1>
      <p className="h-sub">Your money for {monthLabel(monthKey())}, at a glance.</p>

      {/* Net worth + accounts */}
      <div className="card reveal">
        <div className="card-h">Net worth</div>
        <div className={"big " + (nw >= 0 ? "pos" : "neg")} style={{ fontSize: 36, fontWeight: 800, letterSpacing: "-0.03em" }}>
          {formatMoney(nw, data.currency)}
        </div>
        <div className="h-sub" style={{ marginTop: 2, marginBottom: 14 }}>
          {formatMoney(cash, data.currency)} in accounts · {formatMoney(s.totalIOwe, data.currency)} owed
        </div>

        {nwHist.length >= 2 && (
          <Sparkline
            values={nwHist.map((p) => p.value)}
            labels={nwHist.map((p) => monthLabel(p.month).slice(0, 3))}
            color={nw >= 0 ? "#2e8b72" : "#bc5446"}
          />
        )}

        {(data.accounts || []).map((a) => (
          <div className="item" key={a.id}>
            <div className="ic">{a.emoji}</div>
            <div className="meta">
              <div className="t">{a.name}</div>
              <div className="s" style={{ textTransform: "capitalize" }}>{a.type}</div>
            </div>
            <button
              className="amt"
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text)", fontVariantNumeric: "tabular-nums" }}
              onClick={() => {
                const v = prompt(`New balance for ${a.name}:`, String(a.balance));
                if (v != null && !isNaN(parseFloat(v))) updateAccount(a.id, { balance: parseFloat(v) });
              }}
            >
              {formatMoney(a.balance, data.currency)}
            </button>
            <button className="x" onClick={() => deleteAccount(a.id)} aria-label="Delete account">×</button>
          </div>
        ))}

        {acctOpen ? (
          <div style={{ marginTop: 12 }}>
            <div className="field">
              <label>Account name</label>
              <input value={aName} onChange={(e) => setAName(e.target.value)} placeholder="Main checking" autoFocus />
            </div>
            <div className="row">
              <div className="field">
                <label>Type</label>
                <select value={aType} onChange={(e) => setAType(e.target.value as any)}>
                  <option value="checking">Checking</option>
                  <option value="savings">Savings</option>
                  <option value="cash">Cash</option>
                  <option value="investment">Investment</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="field">
                <label>Balance</label>
                <input value={aBalance} onChange={(e) => setABalance(e.target.value)} inputMode="decimal" placeholder="0" />
              </div>
            </div>
            <div className="capture-actions">
              <button className="btn btn-ghost" onClick={() => setAcctOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={saveAccount}>Add account</button>
            </div>
          </div>
        ) : (
          <button className="btn btn-ghost btn-block" style={{ marginTop: 12 }} onClick={() => setAcctOpen(true)}>
            + Add an account
          </button>
        )}
      </div>

      {/* 6-month trend */}
      {trend.some((m) => m.income > 0 || m.expense > 0) && (
        <div className="card reveal d1">
          <div className="card-h">Last 6 months</div>
          <div className="trend">
            {trend.map((m) => (
              <div className="trend-col" key={m.month}>
                <div className="trend-bars">
                  <span className="trend-bar in" style={{ height: `${(m.income / maxFlow) * 100}%` }} title={`In ${formatMoney(m.income, data.currency)}`} />
                  <span className="trend-bar out" style={{ height: `${(m.expense / maxFlow) * 100}%` }} title={`Out ${formatMoney(m.expense, data.currency)}`} />
                </div>
                <div className="trend-label">{m.label}</div>
              </div>
            ))}
          </div>
          <div className="trend-legend">
            <span><i style={{ background: "var(--green)" }} /> In</span>
            <span><i style={{ background: "var(--coral)" }} /> Out</span>
          </div>
        </div>
      )}

      {!hasData ? (
        <div className="card empty-card reveal">
          <div className="empty-emoji">📊</div>
          <div className="empty-title">No data yet</div>
          <p className="h-sub" style={{ textAlign: "center" }}>
            Log a few expenses on the Home screen and your charts will appear
            here — categories, trends, budgets and how spending splits between
            you.
          </p>
        </div>
      ) : (
        <>
          {/* Spending donut */}
          <div className="card reveal d1">
            <div className="card-h">Where your money went</div>
            <div className="donut-wrap">
              <Donut
                slices={slices}
                centerTop={formatMoney(s.expenses, data.currency)}
                centerSub="spent"
              />
              <div className="legend">
                {slices.map((sl) => (
                  <div className="legend-row" key={sl.label}>
                    <span className="swatch" style={{ background: sl.color }} />
                    <span className="legend-label">{sl.label}</span>
                    <span className="legend-val">
                      {formatMoney(sl.value, data.currency)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Month over month */}
          <div className="card reveal d2">
            <div className="card-h">This month vs last</div>
            <div className="mom">
              <div className="mom-col">
                <div className="mom-val">{formatMoney(mom.thisMonth, data.currency)}</div>
                <div className="mom-k">This month</div>
              </div>
              <div className="mom-col">
                <div className="mom-val muted">
                  {formatMoney(mom.lastMonth, data.currency)}
                </div>
                <div className="mom-k">Last month</div>
              </div>
              <div className="mom-col">
                {mom.changePct === null ? (
                  <div className="mom-val muted">—</div>
                ) : (
                  <div className={"mom-val " + (mom.changePct > 0 ? "neg" : "pos")}>
                    {mom.changePct > 0 ? "▲" : "▼"} {Math.abs(Math.round(mom.changePct))}%
                  </div>
                )}
                <div className="mom-k">Change</div>
              </div>
            </div>
          </div>

          {/* Budgets */}
          {budgets.length > 0 && (
            <div className="card reveal d3">
              <div className="card-h">Budgets</div>
              {budgets.map((b) => (
                <div className="bar-row" key={b.category}>
                  <div className="bar-top">
                    <span>{b.category}</span>
                    <span className={b.over ? "neg" : "muted"}>
                      {formatMoney(b.spent, data.currency)} / {formatMoney(b.limit, data.currency)}
                    </span>
                  </div>
                  <div className="bar-track">
                    <div
                      className={"bar-fill" + (b.over ? " over" : "")}
                      style={{ width: `${Math.min(100, b.pct)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Category bars */}
          <div className="card reveal d3">
            <div className="card-h">Top categories</div>
            {cats.slice(0, 8).map((c, i) => (
              <div className="bar-row" key={c.category}>
                <div className="bar-top">
                  <span>{c.category}</span>
                  <span className="muted">{formatMoney(c.amount, data.currency)}</span>
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{
                      width: `${c.pct}%`,
                      background: CHART_COLORS[i % CHART_COLORS.length],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Who spent what */}
          {splits.length > 1 && (
            <div className="card reveal d4">
              <div className="card-h">Who spent what</div>
              {splits.map((sp) => {
                const m = member(sp.memberId);
                return (
                  <div className="split-row" key={sp.memberId}>
                    <Avatar member={m} size={32} />
                    <div className="split-meta">
                      <div className="split-top">
                        <span>{m?.name || "Someone"}</span>
                        <span className="muted">
                          {formatMoney(sp.expenses, data.currency)} ·{" "}
                          {Math.round(sp.pct)}%
                        </span>
                      </div>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${sp.pct}%`,
                            background: m?.color || "#5fe0a6",
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </main>
  );
}
