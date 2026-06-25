"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Landmark,
  Layers,
  LockKeyhole,
  Mic,
  ReceiptText,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useStore } from "@/lib/store";
import { uid, CURRENCIES, MEMBER_COLORS } from "@/lib/format";
import { success } from "@/lib/haptics";
import type { Member } from "@/lib/types";

const FEATURES: Array<{ Icon: LucideIcon; title: string; body: string }> = [
  { Icon: Mic, title: "Just say it", body: "Add expenses, bills, debts — even your salary — by talking." },
  { Icon: Layers, title: "Give every dollar a job", body: "Buckets for savings, investing, tithes, offerings & giving." },
  { Icon: ReceiptText, title: "Snap a receipt", body: "Photos and quick notes become clean entries automatically." },
  { Icon: Sparkles, title: "A coach in your pocket", body: "AI guidance built on your real numbers, not generic tips." },
];

const TOTAL_STEPS = 3;

function num(s: string): number | undefined {
  const n = parseFloat((s || "").replace(/[$,\s]/g, ""));
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

export default function Onboarding() {
  const { completeOnboarding, joinSync } = useStore();
  const [step, setStep] = useState(0);
  const [joining, setJoining] = useState(false);
  const [name, setName] = useState("");
  const [income, setIncome] = useState("");
  const [onHand, setOnHand] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [partner, setPartner] = useState("");
  const [partnerIncome, setPartnerIncome] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [joinBusy, setJoinBusy] = useState(false);
  const [joinError, setJoinError] = useState("");
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [step, joining]);

  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".onb2-rise", { y: 22, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [step, joining]);

  function finish() {
    const me = name.trim() || "Me";
    const members: Member[] = [
      { id: uid(), name: me, emoji: "🦊", color: MEMBER_COLORS[0], monthlyIncome: num(income), updatedAt: Date.now() },
    ];
    if (partner.trim()) {
      members.push({ id: uid(), name: partner.trim(), emoji: "🐧", color: MEMBER_COLORS[1 % MEMBER_COLORS.length], monthlyIncome: num(partnerIncome), updatedAt: Date.now() });
    }
    // Seed a starting cash balance so "safe to spend" is grounded in the money
    // they actually have right now — not their full monthly income. This is what
    // makes the headline accurate when starting mid-month.
    const cash = num(onHand);
    const accounts =
      cash !== undefined
        ? [{ id: uid(), name: "Cash on hand", type: "checking" as const, balance: cash, emoji: "💵", color: MEMBER_COLORS[0], createdAt: Date.now(), updatedAt: Date.now(), balanceAsOf: Date.now() }]
        : undefined;
    success();
    completeOnboarding({
      householdName: name.trim() ? `${me}'s money` : "My money",
      currency,
      members,
      ...(accounts ? { accounts } : {}),
    });
  }

  async function joinHousehold() {
    const code = joinCode.trim();
    if (code.length < 16 || joinBusy) return;
    setJoinBusy(true);
    setJoinError("");
    const r = await joinSync(code);
    setJoinBusy(false);
    if (!r.ok) setJoinError(r.error || "Could not join that household.");
  }

  // ---- Join an existing household ----
  if (joining) {
    return (
      <div className="onb2" ref={root}>
        <div className="onb2-aura" aria-hidden="true" />
        <div className="onb2-inner onb2-rise">
          <div className="onb2-mark"><LockKeyhole size={26} /></div>
          <h1 className="onb2-h1">Join a <span>household</span></h1>
          <p className="onb2-sub">Enter the private code from Settings on the other device. Treat it like a password — it syncs shared budget data.</p>
          <label className="lx-field"><span>Household code</span>
            <input value={joinCode} onChange={(e) => setJoinCode(e.target.value)} placeholder="example-household-code"
              onKeyDown={(e) => e.key === "Enter" && void joinHousehold()} autoFocus />
          </label>
          {joinError && <p className="onb2-err">{joinError}</p>}
          <button className="lx-primary full" onClick={() => void joinHousehold()} disabled={joinBusy || joinCode.trim().length < 16}>
            {joinBusy ? "Joining…" : "Join household"}
          </button>
          <button className="onb2-link" onClick={() => setJoining(false)}><ArrowLeft size={15} /> Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="onb2" ref={root}>
      <div className="onb2-aura" aria-hidden="true" />

      {/* progress dots */}
      <div className="onb2-dots">
        {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
          <span key={i} className={i <= step ? "on" : ""} />
        ))}
      </div>

      {/* STEP 0 — welcome */}
      {step === 0 && (
        <div className="onb2-inner">
          <div className="onb2-hero onb2-rise">
            <div className="onb2-mark big">MC</div>
            <h1 className="onb2-h1">Money that finally <span>makes sense.</span></h1>
            <p className="onb2-sub">A calm, private money app you actually want to open. Talk to it, and it turns your real life into clarity.</p>
          </div>
          <div className="onb2-features">
            {FEATURES.map(({ Icon, title, body }) => (
              <div className="onb2-feature onb2-rise" key={title}>
                <span className="ic"><Icon size={20} /></span>
                <div><strong>{title}</strong><p>{body}</p></div>
              </div>
            ))}
          </div>
          <div className="onb2-actions onb2-rise">
            <button className="lx-primary full" onClick={() => setStep(1)}>Get started <ArrowRight size={18} /></button>
            <button className="onb2-link" onClick={() => setJoining(true)}>Join an existing household</button>
          </div>
          <p className="onb2-privacy onb2-rise"><ShieldCheck size={14} /> Private and on your device by default.</p>
        </div>
      )}

      {/* STEP 1 — you */}
      {step === 1 && (
        <div className="onb2-inner">
          <div className="onb2-rise">
            <div className="onb2-mark"><Sparkles size={24} /></div>
            <h1 className="onb2-h1">Hi — what should I <span>call you?</span></h1>
            <p className="onb2-sub">Just a first name. Everything else is optional, and you can change it anytime.</p>
          </div>
          <label className="lx-field onb2-rise"><span>Your name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Dave" autoFocus />
          </label>
          <label className="lx-field onb2-rise"><span>How much do you have right now?</span>
            <input value={onHand} onChange={(e) => setOnHand(e.target.value)} inputMode="decimal" placeholder="e.g. 19" />
          </label>
          <p className="onb2-hint onb2-rise">Your real checking + cash balance today. This is what makes <b>“safe to spend” accurate</b> — even starting mid-month.</p>
          <label className="lx-field onb2-rise"><span>Monthly take-home income (optional)</span>
            <input value={income} onChange={(e) => setIncome(e.target.value)} inputMode="decimal" placeholder="e.g. 4,200" />
          </label>
          <label className="lx-field onb2-rise"><span>Currency</span>
            <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
              {CURRENCIES.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
            </select>
          </label>
          <div className="onb2-actions onb2-rise">
            <button className="lx-primary full" onClick={() => setStep(2)}>Continue <ArrowRight size={18} /></button>
            <button className="onb2-link" onClick={() => setStep(0)}><ArrowLeft size={15} /> Back</button>
          </div>
        </div>
      )}

      {/* STEP 2 — partner / finish */}
      {step === 2 && (
        <div className="onb2-inner">
          <div className="onb2-rise">
            <div className="onb2-mark"><Landmark size={24} /></div>
            <h1 className="onb2-h1">Sharing money with <span>someone?</span></h1>
            <p className="onb2-sub">Add a partner so spending and plans roll up together. Totally optional — skip if it&apos;s just you.</p>
          </div>
          <label className="lx-field onb2-rise"><span>Partner&apos;s name (optional)</span>
            <input value={partner} onChange={(e) => setPartner(e.target.value)} placeholder="e.g. Sam" />
          </label>
          {partner.trim() && (
            <label className="lx-field onb2-rise"><span>Their monthly income (optional)</span>
              <input value={partnerIncome} onChange={(e) => setPartnerIncome(e.target.value)} inputMode="decimal" placeholder="e.g. 3,000" />
            </label>
          )}
          <div className="onb2-actions onb2-rise">
            <button className="lx-primary full" onClick={finish}><Check size={18} /> Enter Money Coach</button>
            <button className="onb2-link" onClick={() => setStep(1)}><ArrowLeft size={15} /> Back</button>
          </div>
        </div>
      )}
    </div>
  );
}
