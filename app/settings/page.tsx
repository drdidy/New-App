"use client";

import gsap from "gsap";
import { useEffect, useRef, useState } from "react";
import { Download, Plus, Trash2, Upload, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, CURRENCIES, MEMBER_COLORS, MEMBER_EMOJIS } from "@/lib/format";
import Avatar from "@/components/Avatar";
import SyncCard from "@/components/SyncCard";
import type { AppData, PayCycleType } from "@/lib/types";

export default function SettingsPage() {
  const {
    data, ready, setHouseholdName, setCurrency, setPayCycle, setReminders,
    addMember, updateMember, removeMember, setBudget, removeBudget, importData, resetAll,
  } = useStore();
  const [newBudgetCat, setNewBudgetCat] = useState("");
  const [newBudgetLimit, setNewBudgetLimit] = useState("");
  const [note, setNote] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);


  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;
  const cur = data.currency;

  function exportData() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
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
      if (importData(parsed)) flash("Backup restored ✓");
      else flash("That backup couldn't be validated — nothing was changed.");
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
    addMember({ name: "New person", emoji: MEMBER_EMOJIS[i % MEMBER_EMOJIS.length], color: MEMBER_COLORS[i % MEMBER_COLORS.length] });
  }

  function saveBudget() {
    const lim = parseFloat(newBudgetLimit);
    if (!newBudgetCat.trim() || !lim || lim <= 0) return;
    setBudget(newBudgetCat.trim(), lim);
    setNewBudgetCat("");
    setNewBudgetLimit("");
  }

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">You &amp; your setup</p>
      </div>
      <h1 className="pg-title">Settings</h1>
      <div className="pg-rule" />

      {/* PROFILE */}
      <section className="sec rise">
        <div className="sec-head"><h2>Profile</h2></div>
        <label className="field"><span>Profile or household name</span>
          <input value={data.householdName || ""} onChange={(e) => setHouseholdName(e.target.value)} placeholder="David's Money Plan" />
        </label>
        <label className="field"><span>Currency</span>
          <select value={data.currency} onChange={(e) => setCurrency(e.target.value)}>
            {CURRENCIES.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
          </select>
        </label>
        <label className="field"><span>Pay schedule</span>
          <select value={data.payCycle?.type || "monthly"} onChange={(e) => setPayCycle({ type: e.target.value as PayCycleType, anchor: data.payCycle?.anchor })}>
            <option value="monthly">Monthly</option>
            <option value="semimonthly">Twice a month</option>
            <option value="biweekly">Every 2 weeks</option>
            <option value="weekly">Weekly</option>
          </select>
        </label>
        {data.payCycle?.type !== "monthly" && (
          <label className="field"><span>Your next (or last) payday</span>
            <input type="date" value={data.payCycle?.anchor || ""} onChange={(e) => setPayCycle({ type: data.payCycle.type, anchor: e.target.value || undefined })} />
          </label>
        )}
        <label className="toggle">
          <input type="checkbox" checked={Boolean(data.remindersEnabled)}
            onChange={async (e) => {
              const on = e.target.checked;
              if (on && typeof Notification !== "undefined" && Notification.permission === "default") {
                try { await Notification.requestPermission(); } catch {}
              }
              setReminders(on);
            }} />
          <span>Weekly check-in reminders</span>
        </label>
      </section>

      {/* PEOPLE */}
      <section className="sec rise">
        <div className="sec-head"><h2>People in this plan</h2></div>
        <p className="sec-sub" style={{ marginTop: 0 }}>Add people only when their spending is part of this profile.</p>
        {data.members.map((m) => (
          <div className="member" key={m.id}>
            <div className="member-top">
              <Avatar member={m} size={36} />
              <input value={m.name} onChange={(e) => updateMember(m.id, { name: e.target.value })} aria-label="Name" />
              {data.members.length > 1 && (
                <button className="btn-icon danger" onClick={() => { if (confirm(`Remove ${m.name}? Their items move to the remaining person.`)) removeMember(m.id); }} aria-label="Remove person"><X size={15} /></button>
              )}
            </div>
            <div className="emoji-row">
              {MEMBER_EMOJIS.slice(0, 6).map((e) => (
                <button key={e} className={m.emoji === e ? "on" : ""} onClick={() => updateMember(m.id, { emoji: e })}>{e}</button>
              ))}
            </div>
            <div className="color-row">
              {MEMBER_COLORS.map((c) => (
                <button key={c} className={m.color === c ? "on" : ""} style={{ background: c }} onClick={() => updateMember(m.id, { color: c })} aria-label="colour" />
              ))}
            </div>
            <input className="income" key={`inc-${m.id}`} defaultValue={m.monthlyIncome ?? ""} inputMode="decimal" placeholder="Monthly income (optional)"
              onBlur={(e) => {
                // Commit on blur so decimals type naturally ("1200.50" stays intact).
                const n = parseFloat(e.target.value.replace(/[$,\s]/g, ""));
                updateMember(m.id, { monthlyIncome: Number.isFinite(n) && n >= 0 ? n : undefined });
              }} />
          </div>
        ))}
        {data.members.length < 6 && (
          <button className="btn-ghost" style={{ width: "100%", marginTop: 12 }} onClick={addPerson}><Plus size={15} /> Add a person</button>
        )}
      </section>

      <SyncCard />

      {/* BUDGETS */}
      <section className="sec rise">
        <div className="sec-head"><h2>Monthly budgets</h2></div>
        {data.budgets.length === 0 ? (
          <p className="sec-sub" style={{ marginTop: 0 }}>Cap a category and Spending will show progress and warn you.</p>
        ) : data.budgets.map((b) => (
          <div className="row" key={b.category}>
            <span className="row-ic">🎯</span>
            <div className="row-meta"><div className="row-t">{b.category}</div><div className="row-s">{formatMoney(b.limit, cur)} / month</div></div>
            <button className="btn-icon danger" onClick={() => removeBudget(b.category)} aria-label="Remove budget"><Trash2 size={14} /></button>
          </div>
        ))}
        <div className="fieldrow" style={{ marginTop: 14 }}>
          <label className="field"><span>Category</span>
            <input value={newBudgetCat} onChange={(e) => setNewBudgetCat(e.target.value)} placeholder="Dining" />
          </label>
          <label className="field"><span>Limit / month</span>
            <input value={newBudgetLimit} onChange={(e) => setNewBudgetLimit(e.target.value)} inputMode="decimal" placeholder="300" />
          </label>
        </div>
        <button className="btn full" onClick={saveBudget} disabled={!newBudgetCat.trim() || !(parseFloat(newBudgetLimit) > 0)}>Set budget</button>
      </section>

      {/* DATA */}
      <section className="sec rise">
        <div className="sec-head"><h2>Your data</h2></div>
        <p className="sec-sub" style={{ marginTop: 0 }}>Everything lives on this device. Back it up to move phones or keep it safe.</p>
        <div className="fieldrow">
          <button className="btn-ghost" onClick={exportData}><Download size={15} /> Back up</button>
          <button className="btn-ghost" onClick={() => fileRef.current?.click()}><Upload size={15} /> Restore</button>
          <input ref={fileRef} type="file" accept="application/json" hidden onChange={onImport} />
        </div>
        <button className="btn-ghost danger" style={{ width: "100%", marginTop: 10 }}
          onClick={() => { if (confirm("Erase ALL data and start over? This can't be undone.")) resetAll(); }}>
          <Trash2 size={15} /> Erase everything
        </button>
        {note && <p className="flash">{note}</p>}
      </section>

      <p className="colophon">Money Coach — your private money companion</p>
    </main>
  );
}
