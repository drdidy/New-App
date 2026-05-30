"use client";

import { useStore, summarize } from "@/lib/store";
import {
  categoryBreakdown,
  budgetStatus,
  memberSplit,
  monthOverMonth,
} from "@/lib/insights";
import { formatMoney, monthLabel, monthKey } from "@/lib/format";
import Donut from "@/components/Donut";
import Avatar from "@/components/Avatar";

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
  const { data, ready, member } = useStore();
  if (!ready) return null;

  const s = summarize(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);
  const splits = memberSplit(data).filter((x) => x.expenses > 0);
  const mom = monthOverMonth(data);
  const hasData = data.transactions.length > 0;

  const slices = cats.slice(0, 7).map((c, i) => ({
    label: c.category,
    value: c.amount,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <main>
      <h1 className="h-title">Insights</h1>
      <p className="h-sub">Your money for {monthLabel(monthKey())}, at a glance.</p>

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
