"use client";

import { useRef, useState } from "react";
import { useStore } from "@/lib/store";
import {
  formatMoney,
  CURRENCIES,
  MEMBER_COLORS,
  MEMBER_EMOJIS,
} from "@/lib/format";
import Avatar from "@/components/Avatar";
import SyncCard from "@/components/SyncCard";
import type { AppData } from "@/lib/types";

export default function SettingsPage() {
  const {
    data,
    ready,
    setHouseholdName,
    setCurrency,
    setTheme,
    setPayCycle,
    setReminders,
    addMember,
    updateMember,
    removeMember,
    setBudget,
    removeBudget,
    importData,
    resetAll,
  } = useStore();
  const [newBudgetCat, setNewBudgetCat] = useState("");
  const [newBudgetLimit, setNewBudgetLimit] = useState("");
  const [note, setNote] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  if (!ready) return null;

  function exportData() {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `money-coach-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    flash("Backup downloaded ✓");
  }

  async function onImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as AppData;
      if (!parsed || typeof parsed !== "object") throw new Error();
      if (!confirm("Replace all current data with this backup?")) return;
      importData(parsed);
      flash("Backup restored ✓");
    } catch {
      flash("That file didn't look like a valid backup.");
    }
  }

  function flash(msg: string) {
    setNote(msg);
    setTimeout(() => setNote(""), 3500);
  }

  function addPerson() {
    if (data.members.length >= 6) return;
    const i = data.members.length;
    addMember({
      name: "New person",
      emoji: MEMBER_EMOJIS[i % MEMBER_EMOJIS.length],
      color: MEMBER_COLORS[i % MEMBER_COLORS.length],
    });
  }

  function saveBudget() {
    const lim = parseFloat(newBudgetLimit);
    if (!newBudgetCat.trim() || !lim || lim <= 0) return;
    setBudget(newBudgetCat.trim(), lim);
    setNewBudgetCat("");
    setNewBudgetLimit("");
  }

  return (
    <main>
      <h1 className="h-title">You &amp; settings</h1>
      <p className="h-sub">Your household, budgets, and data — all in your control.</p>

      {/* Household */}
      <div className="card reveal">
        <div className="card-h">Household</div>
        <div className="field">
          <label>Household name</label>
          <input
            value={data.householdName || ""}
            onChange={(e) => setHouseholdName(e.target.value)}
            placeholder="The Smith Household"
          />
        </div>
        <div className="field">
          <label>Currency</label>
          <select
            value={data.currency}
            onChange={(e) => setCurrency(e.target.value)}
          >
            {CURRENCIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Appearance</label>
          <div className="seg">
            <button
              className={"seg-btn" + (data.theme === "dark" ? " on" : "")}
              onClick={() => setTheme("dark")}
            >
              🌙 Dark
            </button>
            <button
              className={"seg-btn" + (data.theme === "light" ? " on" : "")}
              onClick={() => setTheme("light")}
            >
              ☀️ Light
            </button>
          </div>
        </div>
        <div className="field">
          <label>Pay schedule</label>
          <select
            value={data.payCycle?.type || "monthly"}
            onChange={(e) =>
              setPayCycle({ type: e.target.value as any, anchor: data.payCycle?.anchor })
            }
          >
            <option value="monthly">Monthly</option>
            <option value="semimonthly">Twice a month</option>
            <option value="biweekly">Every 2 weeks</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        {data.payCycle?.type !== "monthly" && (
          <div className="field">
            <label>Your next (or last) payday</label>
            <input
              type="date"
              value={data.payCycle?.anchor || ""}
              onChange={(e) =>
                setPayCycle({ type: data.payCycle.type, anchor: e.target.value || undefined })
              }
            />
          </div>
        )}
        <label className="toggle">
          <input
            type="checkbox"
            checked={Boolean(data.remindersEnabled)}
            onChange={async (e) => {
              const on = e.target.checked;
              if (on && typeof Notification !== "undefined" && Notification.permission === "default") {
                try { await Notification.requestPermission(); } catch {}
              }
              setReminders(on);
            }}
          />
          <span>Weekly check-in reminders</span>
        </label>
      </div>

      {/* Members */}
      <div className="card reveal d1">
        <div className="card-h">People</div>
        {data.members.map((m) => (
          <div className="member-edit" key={m.id}>
            <Avatar member={m} size={38} />
            <div className="member-fields">
              <input
                className="member-name"
                value={m.name}
                onChange={(e) => updateMember(m.id, { name: e.target.value })}
              />
              <div className="member-sub">
                <div className="emoji-pick">
                  {MEMBER_EMOJIS.slice(0, 6).map((e) => (
                    <button
                      key={e}
                      className={"emoji-opt" + (m.emoji === e ? " on" : "")}
                      onClick={() => updateMember(m.id, { emoji: e })}
                      style={m.emoji === e ? { borderColor: m.color } : undefined}
                    >
                      {e}
                    </button>
                  ))}
                </div>
              </div>
              <div className="color-pick">
                {MEMBER_COLORS.map((c) => (
                  <button
                    key={c}
                    className={"color-opt" + (m.color === c ? " on" : "")}
                    style={{ background: c }}
                    onClick={() => updateMember(m.id, { color: c })}
                    aria-label="colour"
                  />
                ))}
              </div>
              <input
                className="member-income"
                value={m.monthlyIncome ?? ""}
                onChange={(e) =>
                  updateMember(m.id, {
                    monthlyIncome: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                inputMode="decimal"
                placeholder="Monthly income (optional)"
              />
            </div>
            {data.members.length > 1 && (
              <button
                className="x"
                onClick={() => removeMember(m.id)}
                aria-label="Remove person"
              >
                ×
              </button>
            )}
          </div>
        ))}
        {data.members.length < 6 && (
          <button className="btn btn-ghost btn-block" onClick={addPerson} style={{ marginTop: 8 }}>
            + Add a person
          </button>
        )}
      </div>

      {/* Sync */}
      <SyncCard />

      {/* Budgets */}
      <div className="card reveal d2">
        <div className="card-h">Monthly budgets</div>
        {data.budgets.length === 0 && (
          <p className="h-sub" style={{ marginBottom: 12 }}>
            Set a cap on a category and we'll show progress + warn you on the
            Insights screen.
          </p>
        )}
        {data.budgets.map((b) => (
          <div className="item" key={b.category}>
            <div className="ic">🎯</div>
            <div className="meta">
              <div className="t">{b.category}</div>
              <div className="s">{formatMoney(b.limit, data.currency)} / month</div>
            </div>
            <button
              className="x"
              onClick={() => removeBudget(b.category)}
              aria-label="Remove budget"
            >
              ×
            </button>
          </div>
        ))}
        <div className="row" style={{ marginTop: 10 }}>
          <input
            className="mini-input"
            value={newBudgetCat}
            onChange={(e) => setNewBudgetCat(e.target.value)}
            placeholder="Category, e.g. Dining"
          />
          <input
            className="mini-input"
            value={newBudgetLimit}
            onChange={(e) => setNewBudgetLimit(e.target.value)}
            inputMode="decimal"
            placeholder="Limit"
            style={{ maxWidth: 110 }}
          />
        </div>
        <button className="btn btn-ghost btn-block" onClick={saveBudget} style={{ marginTop: 10 }}>
          Set budget
        </button>
      </div>

      {/* Data */}
      <div className="card reveal d3">
        <div className="card-h">Your data</div>
        <p className="h-sub" style={{ marginBottom: 12 }}>
          Everything lives on this device only. Use backup to move it to another
          phone or keep it safe.
        </p>
        <div className="capture-actions" style={{ flexWrap: "wrap" }}>
          <button className="btn btn-ghost" onClick={exportData}>
            ⬇️ Back up
          </button>
          <button className="btn btn-ghost" onClick={() => fileRef.current?.click()}>
            ⬆️ Restore
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json"
            hidden
            onChange={onImport}
          />
        </div>
        <button
          className="btn btn-ghost btn-block danger"
          style={{ marginTop: 10 }}
          onClick={() => {
            if (confirm("Erase ALL data and start over? This can't be undone.")) {
              resetAll();
            }
          }}
        >
          Erase everything
        </button>
        {note && <p className="confirm" style={{ marginTop: 12 }}>{note}</p>}
      </div>

      <p className="hint" style={{ textAlign: "center", marginTop: 4 }}>
        Money Coach · your private money companion 💚
      </p>
    </main>
  );
}
