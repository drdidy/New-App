"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { uid, CURRENCIES, MEMBER_COLORS, MEMBER_EMOJIS } from "@/lib/format";
import type { Member } from "@/lib/types";

interface Draft {
  name: string;
  emoji: string;
  color: string;
  income: string;
}

function blankMember(i: number): Draft {
  return {
    name: "",
    emoji: MEMBER_EMOJIS[i % MEMBER_EMOJIS.length],
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
      .map((p) => ({
        id: uid(),
        name: p.name.trim(),
        emoji: p.emoji,
        color: p.color,
        monthlyIncome: p.income ? parseFloat(p.income) : undefined,
      }));
    if (members.length === 0) {
      members.push({ id: uid(), name: "You", emoji: "🦊", color: MEMBER_COLORS[0] });
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
      <div className="onb">
        <div className="onb-body">
          <div className="onb-step">
            <div className="onb-badge">🔗</div>
            <h1 className="onb-title">Join your household</h1>
            <p className="onb-text">
              Enter the <strong>household code</strong> your partner set up on
              their phone (you'll find it in their Settings → Sync). Your phones
              will then share the same numbers.
            </p>
            <div className="field">
              <input
                autoFocus
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="e.g. otter-maple-river-k4p9x2"
                onKeyDown={(e) => e.key === "Enter" && void joinHousehold()}
              />
            </div>
            {joinError && <p className="err">{joinError}</p>}
            <p className="hint">
              Sync needs the cloud add-on enabled on your app. If nothing appears
              after joining, ask your partner to confirm sync is on.
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
            Join household →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="onb">
      <div className="onb-progress">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <span key={i} className={i <= step ? "on" : ""} />
        ))}
      </div>

      <div className="onb-body" key={step}>
        {step === 0 && (
          <div className="onb-step">
            <div className="onb-badge">💸</div>
            <h1 className="onb-title">Welcome to Money Coach</h1>
            <p className="onb-text">
              A calm, private place to get on top of your money — together. No
              forms to dread: you just talk to it, and your AI coach turns it
              into a plan.
            </p>
            <ul className="onb-list">
              <li>🗣️ Log spending by typing or speaking a sentence</li>
              <li>🤝 Track debts &amp; who owes who</li>
              <li>💬 Get judgment-free advice on your real numbers</li>
              <li>🔒 Everything stays on your device</li>
            </ul>
            <button className="onb-link" onClick={() => setJoining(true)}>
              Joining your partner? Use a household code →
            </button>
          </div>
        )}

        {step === 1 && (
          <div className="onb-step">
            <div className="onb-badge">🏡</div>
            <h1 className="onb-title">What should we call your household?</h1>
            <p className="onb-text">Just a friendly name — you can change it later.</p>
            <div className="field">
              <input
                autoFocus
                value={household}
                onChange={(e) => setHousehold(e.target.value)}
                placeholder="The Smith Household"
                onKeyDown={(e) => e.key === "Enter" && setStep(2)}
              />
            </div>
            <div className="field">
              <label>Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
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
            <div className="onb-badge">👫</div>
            <h1 className="onb-title">Who's in your household?</h1>
            <p className="onb-text">
              Add yourself and your partner. Each person gets their own colour so
              you can see who spent what. Leave the second blank if it's just you.
            </p>
            {people.map((p, i) => (
              <div className="onb-person" key={i}>
                <div className="onb-person-head">
                  <div className="emoji-pick">
                    {MEMBER_EMOJIS.slice(0, 6).map((e) => (
                      <button
                        key={e}
                        type="button"
                        className={"emoji-opt" + (p.emoji === e ? " on" : "")}
                        onClick={() => updatePerson(i, { emoji: e })}
                        style={p.emoji === e ? { borderColor: p.color } : undefined}
                      >
                        {e}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="field">
                  <input
                    value={p.name}
                    onChange={(e) => updatePerson(i, { name: e.target.value })}
                    placeholder={i === 0 ? "Your name" : "Partner's name (optional)"}
                  />
                </div>
                <div className="color-pick">
                  {MEMBER_COLORS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      className={"color-opt" + (p.color === c ? " on" : "")}
                      style={{ background: c }}
                      onClick={() => updatePerson(i, { color: c })}
                      aria-label="colour"
                    />
                  ))}
                </div>
                <div className="field">
                  <label>Monthly income (optional)</label>
                  <input
                    value={p.income}
                    onChange={(e) => updatePerson(i, { income: e.target.value })}
                    inputMode="decimal"
                    placeholder="e.g. 2800"
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {step === 3 && (
          <div className="onb-step">
            <div className="onb-badge">🎉</div>
            <h1 className="onb-title">You're all set</h1>
            <p className="onb-text">
              Here's the trick to actually sticking with it:{" "}
              <strong>don't try to be perfect.</strong> Just open the app and say
              what you spent — even "coffee 4". Do that for a few days and your
              coach will start spotting patterns and giving you a plan.
            </p>
            <div className="onb-tip">
              Try your first one in a second:{" "}
              <em>"spent 40 on gas and I still owe James 200"</em>
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
            Start using Money Coach →
          </button>
        )}
      </div>
    </div>
  );
}
