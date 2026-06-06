"use client";

import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CalendarDays,
  Check,
  ChevronDown,
  ClipboardList,
  CreditCard,
  Eye,
  Flag,
  Globe2,
  LockKeyhole,
  MessageCircle,
  ReceiptText,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useStore } from "@/lib/store";
import { uid, CURRENCIES, MEMBER_COLORS } from "@/lib/format";
import type { Member } from "@/lib/types";

interface Draft {
  name: string;
  color: string;
  income: string;
}

const STEPS = ["Get started", "Your profile", "Add people", "Set your rhythm"];

const SETUP_POINTS: Array<{ title: string; body: string; Icon: LucideIcon }> = [
  {
    title: "Capture spending instantly",
    body: "Type, speak, or scan a receipt and review the result before patterns build up.",
    Icon: ReceiptText,
  },
  {
    title: "Private by design",
    body: "Your numbers stay separate unless you intentionally create or join a shared household.",
    Icon: Users,
  },
  {
    title: "AI guidance that's specific",
    body: "Coach can explain debt payoff options, grocery trends, and weekly next steps.",
    Icon: Sparkles,
  },
  {
    title: "Local-first privacy",
    body: "This browser keeps its own budget unless you choose AI analysis, backup, or sync.",
    Icon: LockKeyhole,
  },
];

const PROFILE_POINTS: Array<{ title: string; body: string; Icon: LucideIcon }> = [
  {
    title: "Private by default",
    body: "Only you can see and manage this profile unless you share a household sync code.",
    Icon: LockKeyhole,
  },
  {
    title: "Separate from other users",
    body: "Your data and settings live in this browser and won't mix with anyone else's.",
    Icon: Users,
  },
  {
    title: "Easy to change later",
    body: "You can update your name, currency, or preferences anytime in settings.",
    Icon: SlidersHorizontal,
  },
];

const RHYTHM_STEPS: Array<{ day: string; title: string; body: string; Icon: LucideIcon }> = [
  { day: "Monday", title: "Check in", body: "Review cash flow and last week's progress.", Icon: ArrowRight },
  { day: "Wednesday", title: "Adjust", body: "Fine-tune spending and upcoming bills.", Icon: BarChart3 },
  { day: "Friday", title: "Plan ahead", body: "Ask Coach for a weekly plan and set your priorities.", Icon: MessageCircle },
  { day: "All week", title: "Stay on track", body: "Get nudges and insights as things change.", Icon: Flag },
];

const RHYTHM_CHECKS: Array<{ title: string; body: string; Icon: LucideIcon }> = [
  { title: "Log a few transactions", body: "Connect accounts or add a few recent transactions.", Icon: ClipboardList },
  { title: "Add bills and subscriptions", body: "Add recurring bills and subscriptions.", Icon: CalendarDays },
  { title: "Add debts and balances", body: "Include loans, credit cards, and other balances.", Icon: CreditCard },
  { title: "Ask Coach for a weekly plan", body: "Coach analyzes your numbers and builds your plan.", Icon: MessageCircle },
];

function blankMember(i: number): Draft {
  return {
    name: "",
    color: MEMBER_COLORS[i % MEMBER_COLORS.length],
    income: "",
  };
}

function StepRail({ step }: { step: number }) {
  return (
    <nav className="launch-steps" aria-label="Setup progress">
      {STEPS.map((label, i) => (
        <div className={"launch-step" + (i === step ? " active" : "") + (i < step ? " done" : "")} key={label}>
          <span>{i < step ? <Check size={14} aria-hidden="true" /> : i + 1}</span>
          <b>{label}</b>
          {i < STEPS.length - 1 && <i aria-hidden="true">...</i>}
        </div>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <div className="launch-brand">
      <span>Mc</span>
      <strong>Money Coach</strong>
    </div>
  );
}

function LaunchShell({
  step,
  children,
  preview,
  actions,
  className = "",
}: {
  step: number;
  children: React.ReactNode;
  preview: React.ReactNode;
  actions: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={"onb professional-onb launch-onb " + className}>
      <StepRail step={step} />
      <div className="launch-grid">
        <section className="launch-copy">{children}</section>
        <aside className="launch-preview">{preview}</aside>
      </div>
      <div className="launch-actions">{actions}</div>
    </div>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button className="launch-btn launch-btn-ghost" onClick={onClick}>
      <ArrowLeft size={20} aria-hidden="true" />
      Back
    </button>
  );
}

function NextButton({
  children = "Continue",
  onClick,
}: {
  children?: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button className="launch-btn launch-btn-primary" onClick={onClick}>
      {children}
      <ArrowRight size={20} aria-hidden="true" />
    </button>
  );
}

function OverviewPreview() {
  return (
    <div className="launch-overview">
      <div className="launch-preview-head">
        <strong>Overview</strong>
        <span>This month <ChevronDown size={12} aria-hidden="true" /></span>
        <em><LockKeyhole size={11} aria-hidden="true" /> Private</em>
      </div>
      <div className="preview-metrics">
        <div>
          <small>Net position</small>
          <b>$24,350</b>
          <span>+ $1,520 vs last month</span>
          <i><TrendingUp size={26} aria-hidden="true" /></i>
        </div>
        <div>
          <small>Spending progress</small>
          <b>68%</b>
          <span>$2,720 of $4,000 budget</span>
          <p><i style={{ width: "68%" }} /></p>
          <small>10 days remaining</small>
        </div>
      </div>
      <div className="preview-chart">
        <div className="launch-preview-head">
          <strong>Cash flow</strong>
          <span>This month <ChevronDown size={12} aria-hidden="true" /></span>
          <label><i /> Income <i /> Expenses <i /> Net</label>
        </div>
        <div className="cash-bars">
          {Array.from({ length: 24 }).map((_, i) => (
            <span key={i} style={{ height: `${22 + ((i * 17) % 58)}px` }}>
              <em style={{ height: `${18 + ((i * 23) % 48)}px` }} />
            </span>
          ))}
          <svg viewBox="0 0 420 140" preserveAspectRatio="none" aria-hidden="true">
            <path d="M8 86 C38 68, 66 92, 94 82 S150 118, 188 92 S244 78, 282 70 S346 42, 412 20" />
            <circle cx="412" cy="20" r="4" />
          </svg>
        </div>
      </div>
      <div className="preview-category">
        <div>
          <small>Top category</small>
          <strong>Groceries</strong>
          <b>$620</b>
          <span>18% of total spending</span>
        </div>
        <i><CreditCard size={34} aria-hidden="true" /></i>
        <svg viewBox="0 0 240 70" preserveAspectRatio="none" aria-hidden="true">
          <path d="M4 54 L28 48 L52 31 L78 42 L102 24 L128 36 L154 17 L182 28 L208 16 L236 10" />
        </svg>
        <em>+ 6% vs last month</em>
      </div>
    </div>
  );
}

function PrivacyPreview() {
  return (
    <div className="privacy-panel">
      <div className="privacy-title">
        <ShieldCheck size={60} aria-hidden="true" />
        <strong>Your data stays private</strong>
      </div>
      {PROFILE_POINTS.map(({ title, body, Icon }) => (
        <div className="privacy-row" key={title}>
          <span><Icon size={27} aria-hidden="true" /></span>
          <div>
            <strong>{title}</strong>
            <p>{body}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function RhythmPreview() {
  return (
    <div className="rhythm-panel">
      <div className="rhythm-left">
        <div className="rhythm-top">
          <span><Sparkles size={25} aria-hidden="true" /></span>
          <div>
            <small>Your weekly rhythm</small>
            <strong>Plan with Coach</strong>
            <p>Review progress, adjust, and stay on track.</p>
          </div>
        </div>
        <div className="rhythm-timeline">
          {RHYTHM_STEPS.map(({ day, title, body, Icon }) => (
            <div className="rhythm-item" key={title}>
              <span><Icon size={24} aria-hidden="true" /></span>
              <div>
                <small>{day}</small>
                <strong>{title}</strong>
                <p>{body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="rhythm-cards">
        <button><Eye size={14} aria-hidden="true" /> Preview</button>
        <div className="week-preview">
          <small>This week preview</small>
          <div className="cash-card">
            <span>Cash flow</span>
            <b>$1,250</b>
            <em>Left to spend</em>
            <div className="tiny-bars">
              {Array.from({ length: 12 }).map((_, i) => <i key={i} style={{ height: `${18 + ((i * 13) % 38)}px` }} />)}
            </div>
          </div>
        </div>
        <div className="priority-card">
          <span><ShieldCheck size={30} aria-hidden="true" /></span>
          <div>
            <small>Top priority</small>
            <strong>Stay ahead of bills</strong>
            <p>You have 2 bills due within 7 days.</p>
            <a>View bills <ArrowRight size={14} aria-hidden="true" /></a>
          </div>
        </div>
        <div className="coach-insight-card">
          <small>Coach insight</small>
          <p>You're on track to reach your monthly goal.</p>
          <span>Keep building momentum.</span>
          <svg viewBox="0 0 260 80" preserveAspectRatio="none" aria-hidden="true">
            <path d="M4 64 L31 58 L58 62 L85 47 L112 43 L139 36 L166 40 L193 21 L220 26 L256 16" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function PeopleCard({
  draft,
  index,
  update,
}: {
  draft: Draft;
  index: number;
  update: (patch: Partial<Draft>) => void;
}) {
  const isPrimary = index === 0;
  return (
    <div className="people-card">
      <div className="people-card-head">
        <span><Users size={31} aria-hidden="true" /></span>
        <div>
          <b>{isPrimary ? "A" : "B"}</b>
          <strong>{isPrimary ? "Primary person" : "Second person"}</strong>
        </div>
      </div>
      <label htmlFor={`person-${index}`}>{isPrimary ? "Your name" : "Partner or household member"}</label>
      <input
        id={`person-${index}`}
        value={draft.name}
        onChange={(e) => update({ name: e.target.value })}
        placeholder={isPrimary ? "Enter your name" : "Enter name (optional)"}
      />
      <label>Choose a color</label>
      <div className="launch-color-pick" aria-label={`${isPrimary ? "Primary" : "Second"} person color`}>
        {MEMBER_COLORS.map((color) => (
          <button
            key={color}
            type="button"
            className={draft.color === color ? "active" : ""}
            style={{ background: color }}
            onClick={() => update({ color })}
            aria-label={`Use color ${color}`}
          />
        ))}
      </div>
      <label htmlFor={`income-${index}`}>Monthly income (optional)</label>
      <div className="money-input">
        <span>$</span>
        <input
          id={`income-${index}`}
          value={draft.income}
          onChange={(e) => update({ income: e.target.value })}
          inputMode="decimal"
          placeholder="e.g. $2,800"
        />
      </div>
    </div>
  );
}

export default function Onboarding() {
  const { completeOnboarding, joinSync } = useStore();
  const [step, setStep] = useState(0);
  const [household, setHousehold] = useState("David's Money Plan");
  const [currency, setCurrency] = useState("USD");
  const [people, setPeople] = useState<Draft[]>([blankMember(0), blankMember(1)]);
  const [joining, setJoining] = useState(false);
  const [joinCode, setJoinCode] = useState("");
  const [joinBusy, setJoinBusy] = useState(false);
  const [joinError, setJoinError] = useState("");

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [step, joining]);

  async function joinHousehold() {
    const code = joinCode.trim();
    if (code.length < 16 || joinBusy) return;
    setJoinBusy(true);
    setJoinError("");
    const result = await joinSync(code);
    setJoinBusy(false);
    if (!result.ok) setJoinError(result.error || "Could not join that household.");
  }

  function updatePerson(i: number, patch: Partial<Draft>) {
    setPeople((current) => current.map((person, idx) => (idx === i ? { ...person, ...patch } : person)));
  }

  function finish() {
    const members: Member[] = people
      .filter((person) => person.name.trim())
      .map((person, i) => ({
        id: uid(),
        name: person.name.trim(),
        emoji: i === 0 ? "A" : "B",
        color: person.color,
        monthlyIncome: person.income ? parseFloat(person.income.replace(/[$,]/g, "")) : undefined,
        updatedAt: Date.now(),
      }));

    if (members.length === 0) {
      members.push({
        id: uid(),
        name: "David",
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

  if (joining) {
    return (
      <LaunchShell
        step={0}
        className="join-screen"
        preview={<PrivacyPreview />}
        actions={
          <>
            <BackButton onClick={() => setJoining(false)} />
            <NextButton onClick={() => void joinHousehold()}>Join household</NextButton>
          </>
        }
      >
        <Brand />
        <h1>Join an existing <em>household</em></h1>
        <p>
          Enter the private household code from Settings on the other device. Treat
          it like a password because it can sync shared budget data.
        </p>
        <div className="profile-form">
          <label htmlFor="join-code">Household code</label>
          <div className="launch-input">
            <LockKeyhole size={22} aria-hidden="true" />
            <input
              id="join-code"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="example-household-code"
              onKeyDown={(e) => e.key === "Enter" && void joinHousehold()}
            />
          </div>
          {joinError && <p className="err">{joinError}</p>}
        </div>
      </LaunchShell>
    );
  }

  if (step === 0) {
    return (
      <LaunchShell
        step={0}
        preview={<OverviewPreview />}
        actions={<NextButton onClick={() => setStep(1)}>Continue</NextButton>}
      >
        <Brand />
        <h1>A smarter operating system for <em>your money.</em></h1>
        <p>
          Build a private monthly plan, invite household members only when you mean
          to share, and use AI when you want numbers turned into next steps.
        </p>
        <div className="launch-capabilities">
          {SETUP_POINTS.map(({ title, body, Icon }) => (
            <div className="launch-capability" key={title}>
              <span><Icon size={26} aria-hidden="true" /></span>
              <div>
                <strong>{title}</strong>
                <p>{body}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="launch-privacy-note">
          <ShieldCheck size={22} aria-hidden="true" />
          <span>Your data stays <strong>private and on your device</strong> by default. You choose what to analyze, share, or sync.</span>
        </div>
        <button className="launch-link" onClick={() => setJoining(true)}>
          Join an existing household <ArrowRight size={16} aria-hidden="true" />
        </button>
      </LaunchShell>
    );
  }

  if (step === 1) {
    return (
      <LaunchShell
        step={1}
        preview={<PrivacyPreview />}
        actions={
          <>
            <BackButton onClick={() => setStep(0)} />
            <NextButton onClick={() => setStep(2)} />
          </>
        }
      >
        <Brand />
        <h1>Create your <em>private</em> profile</h1>
        <p>
          This profile belongs to this browser. It stays private by default and is
          separate from other users unless you intentionally share a household sync code.
        </p>
        <div className="profile-form">
          <label htmlFor="household-name">Profile or household name</label>
          <small>Choose a name that helps you identify this plan.</small>
          <div className="launch-input">
            <Users size={23} aria-hidden="true" />
            <input
              id="household-name"
              value={household}
              onChange={(e) => setHousehold(e.target.value)}
              placeholder="David's Money Plan"
              onKeyDown={(e) => e.key === "Enter" && setStep(2)}
            />
          </div>
          <label htmlFor="currency">Currency</label>
          <small>This is your default currency for tracking and reporting.</small>
          <div className="launch-input select-input">
            <Globe2 size={23} aria-hidden="true" />
            <select id="currency" value={currency} onChange={(e) => setCurrency(e.target.value)}>
              {CURRENCIES.map((option) => (
                <option key={option.code} value={option.code}>{option.label}</option>
              ))}
            </select>
            <ChevronDown size={20} aria-hidden="true" />
          </div>
        </div>
      </LaunchShell>
    );
  }

  if (step === 2) {
    return (
      <LaunchShell
        step={2}
        className="people-step"
        preview={null}
        actions={
          <>
            <BackButton onClick={() => setStep(1)} />
            <NextButton onClick={() => setStep(3)} />
          </>
        }
      >
        <Brand />
        <h1>Add only the people this plan should <em>include</em></h1>
        <p>
          For a personal plan, add yourself. Add a partner or household member only
          when their spending should be visible in the shared plan.
        </p>
        <div className="people-form-grid">
          {people.map((person, i) => (
            <PeopleCard key={i} draft={person} index={i} update={(patch) => updatePerson(i, patch)} />
          ))}
        </div>
        <div className="launch-privacy-note wide">
          <ShieldCheck size={22} aria-hidden="true" />
          <span>Your data stays <strong>private and under your control.</strong> Only the people you add can see their own activity in this shared plan.</span>
        </div>
      </LaunchShell>
    );
  }

  return (
    <LaunchShell
      step={3}
      preview={<RhythmPreview />}
      actions={
        <>
          <BackButton onClick={() => setStep(2)} />
          <NextButton onClick={finish}>Open my plan</NextButton>
        </>
      }
    >
      <Brand />
      <h1>Start with a simple operating <em>rhythm</em></h1>
      <p>
        Log a few real transactions, add your bills and debts, then ask Coach for a
        weekly plan. The app gets more useful as your numbers become more complete.
      </p>
      <div className="rhythm-checklist">
        {RHYTHM_CHECKS.map(({ title, body, Icon: ItemIcon }, i) => {
          return (
            <div className={i === 3 ? "active" : ""} key={title}>
              <span><ItemIcon size={25} aria-hidden="true" /></span>
              <div>
                <strong>{i + 1}. {title}</strong>
                <p>{body}</p>
              </div>
              <i>{i < 3 ? <Check size={22} aria-hidden="true" /> : null}</i>
            </div>
          );
        })}
      </div>
      <div className="launch-privacy-note">
        <ShieldCheck size={22} aria-hidden="true" />
        <span>Your data stays <strong>private and on your device</strong> by default. AI features only analyze the note, receipt image, or financial snapshot you choose to share.</span>
      </div>
    </LaunchShell>
  );
}
