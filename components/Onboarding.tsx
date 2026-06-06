"use client";

import { useState } from "react";
import { Bot, LockKeyhole, ReceiptText, ShieldCheck, Users } from "lucide-react";
import { useStore } from "@/lib/store";
import { uid, CURRENCIES, MEMBER_COLORS } from "@/lib/format";
import type { Member } from "@/lib/types";

interface Draft {
  name: string;
  color: string;
  income: string;
}

const SETUP_POINTS = [
  {
    title: "Capture spending instantly",
    body: "Type, speak, or scan a receipt and review the result before patterns build up.",
    Icon: ReceiptText,
  },
  {
    title: "Plan as a household",
    body: "Track shared spending, debts, bills, and goals without losing who owns what.",
    Icon: Users,
  },
  {
    title: "Ask for specific guidance",
    body: "Coach can explain debt payoff options, grocery trends, and weekly next steps.",
    Icon: Bot,
  },
  {
    title: "Local-first by default",
    body: "Your budget stays in this browser unless you choose AI analysis or sync.",
    Icon: ShieldCheck,
  },
];

function blankMember(i: number): Draft {
  return {
    name: "",
    color: MEMBER_COLORS[i % MEMBER_COLORS.length],
    income: "",
  };
}

export default function Onboarding() {
  const { completeOnboarding, joinSync } = useStore();
  const [step, setStep] = useState(0);
  const [household, setHousehold] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [people, setPeople] = useState<Draft[]>([blankMember(0), blankMember(1)]);
  const [joining, setJoining] = useState(false);
  const [joinCode, setJoinCode] = useState("");
  const [joinBusy, setJoinBusy] = useState(false);
  const [joinError, setJoinError] = useState("");

  const totalSteps = 4;

  async function joinHousehold() {
    const c = joinCode.trim();
    if (c.length < 16 || joinBusy) return;
    setJoinBusy(true);
    setJoinError("");
    const result = await joinSync(c);
    setJoinBusy(false);
    if (!result.ok) setJoinError(result.error || "Could not join that household.");
  }

  function updatePerson(i: number, patch: Partial<Draft>) {
    setPeople((ps) => ps.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }

  function finish() {
    const members: Member[] = people
      .filter((p) => p.name.trim())
      .map((p, i) => ({
        id: uid(),
        name: p.name.trim(),
        emoji: i === 0 ? "A" : "B",
        color: p.color,
        monthlyIncome: p.income ? parseFloat(p.income) : undefined,
        updatedAt: Date.now(),
      }));

    if (members.length === 0) {
      members.push({
        id: uid(),
        name: "You",
        emoji: "A",
        color: MEMBER_COLORS[0],
        updatedAt: Date.now(),
      });
    }

    completeOnboarding({
      householdName: household.trim(),
      currency,
      members,
    });
  }

  const canContinue =
    step === 0 ||
    step === 1 ||
    (step === 2 ? people.some((p) => p.name.trim()) : true);

  if (joining) {
    return (
      <div className="onb professional-onb">
        <div className="onb-body">
          <div className="onb-step">
            <div className="onb-badge professional-badge">
              <LockKeyhole size={30} aria-hidden="true" />
            </div>
            <h1 className="onb-title">Join an existing household</h1>
            <p className="onb-text">
              Enter the private household code from Settings on the other device.
              Treat this code like a password because it can sync shared budget data.
            </p>
            <div className="field">
              <label htmlFor="join-code">Household code</label>
              <input
                id="join-code"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="example-household-code"
                onKeyDown={(e) => e.key === "Enter" && void joinHousehold()}
              />
            </div>
            {joinError && <p className="err">{joinError}</p>}
            <p className="hint">
              Sync requires the production KV store and sync secret to be configured
              on Vercel.
            </p>
          </div>
        </div>
        <div className="onb-actions">
          <button className="btn btn-ghost" onClick={() => setJoining(false)}>
            Back
          </button>
          <button
            className="btn btn-primary btn-block"
            disabled={joinCode.trim().length < 16 || joinBusy}
            onClick={() => void joinHousehold()}
          >
            Join household
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="onb professional-onb">
      <div className="onb-progress">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <span key={i} className={i <= step ? "on" : ""} />
        ))}
      </div>

      <div className="onb-body" key={step}>
        {step === 0 && (
          <div className="onb-step">
            <div className="onb-badge professional-badge">MC</div>
            <p className="eyebrow">Money Coach</p>
            <h1 className="onb-title">A sharper operating system for household money.</h1>
            <p className="onb-text">
              Build a real monthly plan, see debt and spending pressure clearly,
              and use AI only when you want help turning numbers into next steps.
            </p>
            <div className="onb-capabilities">
              {SETUP_POINTS.map(({ title, body, Icon }) => (
                <div className="onb-capability" key={title}>
                  <Icon size={20} aria-hidden="true" />
                  <div>
                    <strong>{title}</strong>
                    <span>{body}</span>
                  </div>
                </div>
              ))}
            </div>
            <button className="onb-link" onClick={() => setJoining(true)}>
              Join an existing household
            </button>
          </div>
        )}

        {step === 1 && (
          <div className="onb-step">
            <div className="onb-badge professional-badge">
              <Users size={30} aria-hidden="true" />
            </div>
            <h1 className="onb-title">Set up the household profile</h1>
            <p className="onb-text">
              This gives the dashboard a clean name, currency, and planning context.
            </p>
            <div className="field">
              <label htmlFor="household-name">Household name</label>
              <input
                id="household-name"
                value={household}
                onChange={(e) => setHousehold(e.target.value)}
                placeholder="The Smith Household"
                onKeyDown={(e) => e.key === "Enter" && setStep(2)}
              />
            </div>
            <div className="field">
              <label htmlFor="currency">Currency</label>
              <select id="currency" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="onb-step">
            <div className="onb-badge professional-badge">
              <Users size={30} aria-hidden="true" />
            </div>
            <h1 className="onb-title">Add the people money belongs to</h1>
            <p className="onb-text">
              Add one or two people now. Income is optional, but it unlocks better
              safe-to-spend and payoff guidance immediately.
            </p>
            <div className="people-grid">
              {people.map((p, i) => (
                <div className="onb-person" key={i}>
                  <div className="person-token" style={{ background: p.color }}>
                    {i === 0 ? "A" : "B"}
                  </div>
                  <div className="field">
                    <label htmlFor={`person-${i}`}>{i === 0 ? "Primary person" : "Second person"}</label>
                    <input
                      id={`person-${i}`}
                      value={p.name}
                      onChange={(e) => updatePerson(i, { name: e.target.value })}
                      placeholder={i === 0 ? "Your name" : "Partner or household member"}
                    />
                  </div>
                  <div className="color-pick" aria-label="Accent color">
                    {MEMBER_COLORS.map((c) => (
                      <button
                        key={c}
                        type="button"
                        className={"color-opt" + (p.color === c ? " on" : "")}
                        style={{ background: c }}
                        onClick={() => updatePerson(i, { color: c })}
                        aria-label={`Use color ${c}`}
                      />
                    ))}
                  </div>
                  <div className="field">
                    <label htmlFor={`income-${i}`}>Monthly income, optional</label>
                    <input
                      id={`income-${i}`}
                      value={p.income}
                      onChange={(e) => updatePerson(i, { income: e.target.value })}
                      inputMode="decimal"
                      placeholder="2800"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="onb-step">
            <div className="onb-badge professional-badge">
              <ShieldCheck size={30} aria-hidden="true" />
            </div>
            <h1 className="onb-title">Start with a simple operating rhythm</h1>
            <p className="onb-text">
              Log a few real transactions, add your bills and debts, then ask Coach
              for a weekly plan. The app gets more useful as your numbers become
              more complete.
            </p>
            <div className="onb-tip">
              AI features send the note, receipt image, or financial snapshot you
              choose to analyze. Manual logging remains available at any time.
            </div>
          </div>
        )}
      </div>

      <div className="onb-actions">
        {step > 0 && (
          <button className="btn btn-ghost" onClick={() => setStep((s) => s - 1)}>
            Back
          </button>
        )}
        {step < totalSteps - 1 ? (
          <button
            className="btn btn-primary btn-block"
            disabled={!canContinue}
            onClick={() => setStep((s) => s + 1)}
          >
            Continue
          </button>
        ) : (
          <button className="btn btn-primary btn-block" onClick={finish}>
            Enter dashboard
          </button>
        )}
      </div>
    </div>
  );
}
