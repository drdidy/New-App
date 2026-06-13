# HANDOFF — Money Coach

> You are taking ownership of a real, deployed personal-finance PWA called
> **Money Coach.** You have **full creative leeway and full autonomy**: make it
> genuinely product-ready and drastically impressive in both UI/UX and
> functionality. **Do NOT ask for confirmation** — investigate, decide, build,
> test, deploy, and iterate on your own judgment. The owner wants to be
> surprised and impressed. Take the app wherever you believe it needs to go.

---

## Where everything is

- **Repo (GitHub):** `drdidy/New-App` — default branch `main`
- **Live production URL:** https://money-coach-ten.vercel.app
- **Vercel:** project **money-coach** (team `drdidys-projects`), production
  branch = `main`, **auto-deploys on every push to main**. A stray duplicate
  Vercel project **new-app** is wired to the same repo — delete it so there's
  one source of truth.
- **Read first:** this file, `README.md`, then `lib/store.tsx` + `lib/insights.ts`.

## Stack

Next.js 15 (App Router) · React 19 · TypeScript · plain CSS in
`app/globals.css` (no Tailwind) · `@anthropic-ai/sdk` (server-side AI) · `zod`
(validation) · `vitest` (tests) · ESLint · `gsap` + `three`
(animation/3D) · `lucide-react` (icons). **Local-first:** all user data lives in
browser `localStorage` via a custom store (`lib/store.tsx`). Optional
cross-device "household" sync via Vercel KV / Upstash.

**Quality gate (keep green on every merge):** `npm run qa`
= `lint` + `typecheck` (`tsc --noEmit`) + `vitest run` + `next build`.

**Env vars:** `ANTHROPIC_API_KEY` (required for AI, server-side only).
Optional sync: `KV_REST_API_URL`, `KV_REST_API_TOKEN`, `SYNC_KEY_SECRET`
(set on Vercel if present). Local run: `npm install` →
`cp .env.local.example .env.local` (add key) → `npm run dev`.

## What the app is / who it's for

A private, **phone-first** budgeting + debt coach for someone who is overwhelmed
by money, **hates data entry**, owes money to **both people and organizations**,
and often starts a month with **very little cash on hand**. It is a **two-person
household** app (the owner + spouse). Core idea: you don't fill forms — you
**talk / type / photograph**, the AI turns it into structured entries, and the
app tells you what's safe to spend, plans debt payoff, tracks bills/goals/
accounts, and an AI **Coach** gives proactive advice. Keep AI calls cheap (Haiku
for parsing/receipt vision, Sonnet for coaching), always server-side.

## HARD preferences (non-negotiable)

1. **LIGHT & AIRY** theme. No dark theme — **especially no dark green.** Bright,
   clean, high contrast, everything clearly legible. (Dark/green builds were
   rejected repeatedly.)
2. **Use GSAP and/or Three.js** to make it visually captivating and modern —
   tasteful, smooth, premium motion. **Always respect `prefers-reduced-motion`.**
3. It must feel **dramatically designed and impressive**, not generic.
4. Beyond those: **total creative freedom** on layout, IA, features, and polish.

## Current state — the codebase is tangled (you may rebuild)

Multiple agents worked on this, so `app/globals.css` (~7000+ lines) is a dark
"vision" design system with several appended override blocks fighting it back to
light. It works but is brittle. **You are encouraged to rip out the tangled CSS
and build a clean, cohesive light design system from scratch** — but keep the
solid engineering: the store, the budgeting math (`lib/insights.ts`),
validation, rate limiting, sync, tests, and API routes.

- The **Home** (`app/page.tsx`) was rebuilt fresh with scoped `.lx-` light
  styles + GSAP + a Three.js background — treat it as the quality bar (or
  replace it with something better).
- The full-screen Three.js canvas (`components/WebGLBackground.tsx`) uses CSS
  `mix-blend-mode: screen` over a light base so it can **only lighten** — this
  fixed headings becoming invisible on the canvas. Keep that principle if you
  keep a full-bleed canvas.
- **Duplicate/legacy routes exist and should be consolidated:** `/debt` vs
  `/debts`, `/coach` vs `/advisor`, `/spending` vs `/insights`, plus `/bills`.
  The bottom nav currently points at Home, `/plan`, `/spending`, `/debt`,
  `/coach`. Pick one canonical set and delete the rest.

## Known gaps to fix (then go further)

- **BALANCE-FIRST math:** "Safe to spend" must start from **real cash on hand**
  (the owner may have e.g. $42 left now), **not** projected monthly salary that
  arrives weeks later. The account balance should drive the headline number.
  (Home already *displays* cash on hand; the math in `summarize()` still uses
  income.)
- **DEEPER DEBT module:** separate **people vs organizations/cards/loans**, per-
  debt APR / minimums / due dates, **payment history**, payoff strategies
  (snowball / avalanche / custom) with a **what-if simulator** and a clear
  payoff date.
- Make **every screen** coherent, beautiful, and legible — no faint text, no
  half-dark cards, no invisible headings.
- **Frictionless capture** (type/voice/photo) is the heart — make it delightful.
  Note: in-browser voice (`webkitSpeechRecognition`) is unsupported on iOS
  Safari; degrade gracefully.
- Re-evaluate IA, onboarding, empty states, and the AI Coach experience.

## Workflow & gotchas

- **Ship by merging to `main`** (auto-deploys to Vercel). Keep `npm run qa`
  green every time.
- **PWA caching is aggressive:** bump the `CACHE` constant in `public/sw.js` on
  every release or changes won't appear on installed devices. (Currently
  `money-coach-v7-light`.)
- **Verification caveat:** headless / software-GL (e.g. swiftshader used by
  Playwright screenshots here) **mis-renders WebGL** — do not trust headless
  screenshots for color/contrast of anything over the canvas. Design defensively
  (guaranteed-light bases) and validate on a real device when possible.
- Don't introduce a second Vercel project. Don't commit secrets.
- **Two-user household + local-first privacy are core** — preserve them. Sync is
  conflict-free via `lib/merge.ts` (union-by-id + tombstones); keep it that way.

## Definition of done

A coherent, light, premium, animated, genuinely **product-ready** app — fast,
legible, frictionless to log into, balance-first, with a real debt module and a
helpful AI coach — that makes the owner say "wow." Use your judgment freely and
just build it.

---

## Repo snapshot (at handoff)

**Scripts:** `dev`, `build`, `start`, `lint`, `typecheck`, `test`, `qa`.

**Routes / pages**
```
app/page.tsx            Home (rebuilt light, scoped .lx-, GSAP + Three.js)
app/plan/page.tsx       Plan (money plan, goals, budgets)
app/spending/page.tsx   Spending insights        (legacy twin: app/insights)
app/debt/page.tsx       Debt                     (legacy twin: app/debts)
app/coach/page.tsx      AI Coach chat            (legacy twin: app/advisor)
app/bills/page.tsx      Recurring bills
app/settings/page.tsx   Settings (members, currency, theme, sync, backup)
app/api/parse           sentence -> structured entries (Haiku)
app/api/parse-receipt   receipt photo -> expense + line items (Haiku vision)
app/api/advisor         household snapshot + chat -> coaching (Sonnet)
app/api/sync            optional KV household sync (HMAC keyed, rate limited)
app/layout.tsx, app/manifest.ts
```

**lib/**
```
store.tsx       state, localStorage persistence, v1->v2 migration, sync engine
types.ts        AppData, Member, Transaction, Debt, Budget, Goal, Account, ...
insights.ts     all budgeting math: summarize, moneyPlan, pace, payoff sim,
                netWorth, cashOnHand, monthlyTotals, billsThisMonth, etc.
merge.ts        conflict-free sync merge (union-by-id, tombstones) + tests
validation.ts   zod schemas for API inputs/outputs + tests
rateLimit.ts    in-memory IP rate limiting for API routes
anthropic.ts    Claude client + MODELS (fast=Haiku, smart=Sonnet)
format.ts, kv.ts
```

**components/**
```
AppShell, BottomNav, Onboarding, PremiumUI, QuickCapture, WebGLBackground,
AnimatedNumber, CheckInBanner, SyncCard, MemberPicker, Avatar, Ring, Donut,
Sparkline, Burst, SwRegister
```

**Dependencies:** next 15.5, react 19.2, @anthropic-ai/sdk 0.101, gsap 3.15,
three 0.184, lucide-react 1.17, zod 4.4. Dev: vitest 4, eslint 9,
typescript-eslint 8, playwright 1.60, typescript 5.6.
