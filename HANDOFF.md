# HANDOFF — Money Coach

> You have **complete creative and technical authority** over this project.
> Your one mandate: take "Money Coach" wherever you believe it should go and
> make it a **genuinely product-ready app that impresses me.** Surprise me.
>
> **Nothing below is a restriction.** Redesign it, re-architect it, rename it,
> change the theme, the stack, the data model, the whole concept of a screen —
> whatever your taste and judgment call for. If anything here conflicts with a
> better idea you have, **ignore it and do the better thing.** Do not ask me to
> confirm anything — investigate, decide, build, test, deploy, iterate. Own it.

The only genuine guardrails (everything else is yours):
- It's my **private personal-finance** app — keep my data safe and never leak
  secrets/keys.
- **Shipping works by merging to `main`** (auto-deploys to Vercel). Keep the
  build working so deploys succeed.
- Everything else — design, features, structure, even direction — is your call.

---

## Orientation (facts, not rules)

- **Repo:** `drdidy/New-App` — default branch `main`
- **Live URL:** https://money-coach-ten.vercel.app
- **Vercel:** project **money-coach** (team `drdidys-projects`), production
  branch `main`, auto-deploys on push. A stray duplicate project **new-app** is
  also wired to the repo — delete it if you want one clean deploy.
- **Current stack:** Next.js 15 (App Router) · React 19 · TypeScript · plain CSS
  (`app/globals.css`) · `@anthropic-ai/sdk` · `zod` · `vitest` · ESLint · `gsap`
  + `three` · `lucide-react`. Local-first: data in `localStorage`
  (`lib/store.tsx`); optional Vercel KV / Upstash sync. **You may swap any of
  this** if you have a better foundation.
- **Build/test:** `npm run qa` = lint + typecheck + vitest + build. Run locally:
  `npm install` → `cp .env.local.example .env.local` (add key) → `npm run dev`.
- **Env:** `ANTHROPIC_API_KEY` (server-side AI). Optional sync: `KV_REST_API_URL`,
  `KV_REST_API_TOKEN`, `SYNC_KEY_SECRET`.

## What it's for (the human problem to solve — solve it however you like)

A private, phone-first money app for someone **overwhelmed** by budgeting and
debt, who **hates data entry**, owes money to **both people and organizations**,
and often has **very little cash on hand mid-month**. It's a **two-person
household** (me + my spouse). The spirit so far: don't make me fill forms — let
me talk / type / photograph, and have the app + an AI coach turn that into
clarity (what's safe to spend, a debt plan, bills, goals) with proactive advice.
Keep that *problem* in mind, but solve it any way you think is best.

## My taste so far (FYI only — overrule freely)

These are things I reacted to in earlier iterations. They are **not
requirements** — if your vision is stronger, follow yours:
- I gravitated toward a **light, airy, premium** feel and disliked a dark-green
  build. (But if you can make dark *stunning*, prove me wrong.)
- I like **tasteful motion** (GSAP / Three.js) when it elevates the product, not
  decoration for its own sake. Respect `prefers-reduced-motion`.
- Two unmet asks I'd love solved: **"safe to spend" driven by real cash on hand**
  (not future salary), and a **much deeper debt module** (people vs orgs/cards,
  APR, due dates, payment history, payoff strategies + what-if). Implement them
  your way — or do something better that makes them irrelevant.

## State of the code (so you don't trip, not to constrain you)

Multiple agents worked here, so it's uneven. `app/globals.css` (~7000+ lines)
is a tangle of an old dark design system with light overrides layered on top —
**feel free to delete it and build a clean design system from scratch.** The
Home (`app/page.tsx`) was rebuilt with scoped `.lx-` light styles + GSAP + a
screen-blended Three.js canvas (`mix-blend-mode: screen` keeps text legible over
the canvas) — keep, replace, or ignore. There are **duplicate/legacy routes**
(`/debt` vs `/debts`, `/coach` vs `/advisor`, `/spending` vs `/insights`, plus
`/bills`) — consolidate as you see fit. The engineering worth reusing if you
want it: store, budgeting math (`lib/insights.ts`), conflict-free sync merge
(`lib/merge.ts`), validation (`lib/validation.ts`), rate limiting, tests, API
routes. Reuse none, some, or all.

## Practical notes

- PWA caching is aggressive — if you keep the service worker, bump the `CACHE`
  constant in `public/sw.js` on each release or installed devices won't update.
- Headless/software-GL (Playwright screenshots here) **mis-renders WebGL** —
  don't trust headless screenshots for color/contrast over a canvas; validate on
  a real device when you can.

## Definition of done

A polished, product-ready app that makes me say **"wow."** That's the whole
brief. Everything else is your canvas — go.

---

## Repo snapshot (at handoff)

**Scripts:** `dev`, `build`, `start`, `lint`, `typecheck`, `test`, `qa`.

**Routes**
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
insights.ts     budgeting math: summarize, moneyPlan, pace, payoff sim,
                netWorth, cashOnHand, monthlyTotals, billsThisMonth, ...
merge.ts        conflict-free sync merge (union-by-id, tombstones) + tests
validation.ts   zod schemas + tests · rateLimit.ts · anthropic.ts (models)
format.ts · kv.ts
```

**components/** AppShell, BottomNav, Onboarding, PremiumUI, QuickCapture,
WebGLBackground, AnimatedNumber, CheckInBanner, SyncCard, MemberPicker, Avatar,
Ring, Donut, Sparkline, Burst, SwRegister

**Deps:** next 15.5, react 19.2, @anthropic-ai/sdk 0.101, gsap 3.15, three 0.184,
lucide-react 1.17, zod 4.4; dev: vitest 4, eslint 9, playwright 1.60, typescript 5.6.
