# Money Coach Architecture

This is a handoff map for a fresh developer or coding AI. Start with
`README.md` for setup, then use this file to understand how the app is put
together and where to make changes.

## Product Summary

Money Coach is a phone-first budgeting and debt-coaching PWA. The core
experience is low-friction capture: users type, speak, or photograph a receipt,
then Claude turns that into transactions or debts. The app keeps financial data
local by default in browser `localStorage`, with optional household sync through
KV/Upstash.

The app supports one or more household members, recurring bills, category
budgets, savings goals, accounts, debts/IOUs, insights, and an AI advisor that
receives a live financial snapshot.

## Stack

- Next.js 15 App Router
- React 19
- TypeScript
- Anthropic SDK for parse, receipt vision, and advisor routes
- Browser `localStorage` for primary persistence
- Optional Upstash/Vercel KV over REST for multi-device sync
- PWA manifest plus a static service worker in `public/sw.js`

Important npm scripts:

```bash
npm install
npm run dev
npm run build
```

Environment variables:

```bash
ANTHROPIC_API_KEY=...
KV_REST_API_URL=...      # optional sync
KV_REST_API_TOKEN=...    # optional sync
```

## Directory Map

```text
app/
  api/
    advisor/route.ts        AI coach endpoint
    parse/route.ts          natural-language transaction/debt parser
    parse-receipt/route.ts  receipt image parser
    sync/route.ts           optional KV-backed household sync
  advisor/page.tsx          chat UI and financial snapshot builder
  bills/page.tsx            recurring bills UI
  debts/page.tsx            debts, IOUs, payoff plans, what-if simulator
  insights/page.tsx         charts, account balances, net worth, trends
  plan/page.tsx             monthly allocation, goals, spending budgets
  settings/page.tsx         household, people, theme, backup/restore, sync
  page.tsx                  home dashboard and quick capture
  layout.tsx                app shell/provider wiring
  manifest.ts               PWA manifest

components/
  AppShell.tsx              common app frame, onboarding, bottom nav
  QuickCapture.tsx          text/voice/receipt capture
  SyncCard.tsx              sync setup/status UI
  Onboarding.tsx            first-run setup
  charts/visual helpers     Donut, Sparkline, Ring, AnimatedNumber, etc.

lib/
  types.ts                  canonical data model
  store.tsx                 client store, persistence, mutations, sync loop
  merge.ts                  conflict merge and sync sanitization
  insights.ts               budgeting math, summaries, forecasts, payoff sim
  anthropic.ts              server-side Anthropic client/model selection
  kv.ts                     server-side KV REST helper
  format.ts                 dates, ids, currency, colors, formatting helpers

public/
  icons and sw.js           installable PWA assets
```

## Data Model

The canonical shape is `AppData` in `lib/types.ts`.

Top-level entities:

- `Member`: household participant with name, emoji, color, optional income.
- `Transaction`: income or expense. Amounts are always positive; `type` carries
  direction.
- `Debt`: either `i_owe` or `owed_to_me`, with optional APR, minimum payment,
  due date, owner, and original balance.
- `Budget`: monthly category spending cap.
- `Goal`: savings pot with target, saved amount, and optional monthly
  contribution.
- `RecurringBill`: fixed monthly commitment, due day, optional owner, optional
  auto-log.
- `Account`: cash/checking/savings/investment balance for net worth.
- `PayCycle`: monthly, semimonthly, biweekly, or weekly period logic.
- `NetWorthPoint`: monthly historical net-worth snapshot.

Sync-related fields:

- `tombstones`: deleted ids or `budget:<category>` markers so deletes propagate.
- `settingsUpdatedAt`: last-write-wins clock for scalar settings.
- `syncCode` and `syncEnabled`: local-only settings, stripped before cloud sync.

## Client Store And Persistence

`lib/store.tsx` is the app's client-side state layer. It exposes `useStore()`
through `StoreProvider`.

Key responsibilities:

- Creates fresh v2 data with `freshData()`.
- Migrates older or partial saved blobs with `migrate()`.
- Loads from `localStorage` key `money-coach-data-v1` on mount.
- Saves every data change back to `localStorage`.
- Reflects `data.theme` on `<html data-theme="...">`.
- Auto-logs recurring bills whose due date has arrived and `autoLog` is enabled.
- Records or refreshes the current month's net-worth snapshot.
- Provides mutations for transactions, debts, members, budgets, bills, goals,
  accounts, pay cycle, settings, import/export, reset, and sync.

Important derived selectors in `store.tsx`:

- `summarize(data, memberId?)`: current-month income, expenses, debts, unpaid
  bills, and safe-to-spend.
- `unpaidBills(data, memberId?)`: recurring bills not yet paid this month.

Mutation convention:

- New records get `id: uid()` and `createdAt: Date.now()`.
- Deletes append tombstones.
- Debt payments against `i_owe` also create an expense transaction.
- Goal contributions also create a `Savings` expense transaction.
- Parsed entries from the AI are applied via `applyParsedEntries()`.

## Budgeting And Insight Math

`lib/insights.ts` is the pure calculation layer. It should stay framework-free
and easy to test.

Important functions:

- `baselineIncome()`: logged income for the month, otherwise member income or
  legacy global income.
- `moneyPlan()`: zero-based monthly allocation across bills, debt minimums,
  savings goals, budgets, and leftover.
- `pace()`: safe-to-spend as daily allowance through the current pay period,
  plus projected month-end spend.
- `billsThisMonth()`: recurring bill status and due-date distance.
- `categoryBreakdown()`, `budgetStatus()`, `memberSplit()`,
  `monthOverMonth()`: chart and insight inputs.
- `cashOnHand()` and `netWorth()`: account and debt rollups.
- `monthlyTotals()`: six-month income/expense trend source.
- `cycleInfo()`: pay-cycle period end and days remaining.
- `simulatePayoff()` and `payoffPlan()`: debt what-if and ordering logic.
- `quickInsights()`: short dashboard nudges.

## AI Flow

All Anthropic calls happen server-side, so the API key is never shipped to the
browser. Shared setup is in `lib/anthropic.ts`.

Model roles:

- `MODELS.fast`: high-volume structured extraction and receipt parsing.
- `MODELS.smart`: advisor/coach reasoning.
- `MODELS.deep`: reserved, not used by default.

Routes:

- `POST /api/parse`
  - Input: `{ text }`
  - Uses a JSON-schema-constrained Claude response.
  - Returns `{ entries: ParsedEntry[] }`.
  - `QuickCapture` passes the result to `applyParsedEntries()`.

- `POST /api/parse-receipt`
  - Input: `{ image: dataUrl }`
  - Accepts png, jpeg/jpg, webp, or gif data URLs.
  - Returns a single receipt expense candidate.
  - `QuickCapture` adds it as a transaction.

- `POST /api/advisor`
  - Input: `{ messages, snapshot }`
  - `app/advisor/page.tsx` constructs the snapshot from store data and
    `lib/insights.ts` calculations.
  - Returns `{ reply }`.

The advisor snapshot includes household members, summary, currency, money plan,
pace, net worth, cash on hand, goals, budgets, top categories, month-over-month
data, recurring bills, debts, and recent expenses.

## Optional Sync

Sync is intentionally small and optional.

Client side:

- `SyncCard` lets the user enable sync with a shared household code.
- `store.tsx` debounces local pushes, polls every 12 seconds, and syncs on
  window focus.
- If `/api/sync` reports `configured: false`, sync state becomes
  `unconfigured` and the app remains local-only.

Server side:

- `app/api/sync/route.ts` handles `status`, `pull`, and `push`.
- Household blobs are stored under `mc:household:<clean-code>`.
- `lib/kv.ts` talks to Upstash/Vercel KV over REST.

Merge behavior:

- `lib/merge.ts` unions collections by id or category.
- Tombstones remove deleted records after union.
- If the same id exists on both sides, the newer record wins by `createdAt` for
  most collections.
- Scalar settings use the copy with the larger `settingsUpdatedAt`.
- `sanitizeForSync()` strips local-only sync settings before writing the shared
  blob.

This is suitable for a low-write household app. It is not a full CRDT.

## Screen Responsibilities

`app/page.tsx`

- Home dashboard.
- Shows safe-to-spend, income/outflow, daily pace, debt totals, quick insights,
  quick capture, upcoming bills, recent transactions, and coach CTA.
- Supports member filtering for multi-person households.

`components/QuickCapture.tsx`

- Handles text submission to `/api/parse`.
- Handles browser speech recognition and auto-submits final dictated text.
- Handles receipt upload/camera capture to `/api/parse-receipt`.
- Applies parsed entries or adds receipt transactions to the store.

`app/plan/page.tsx`

- Shows zero-based monthly allocation from `moneyPlan()`.
- Manages savings goals and category budgets.
- Links to recurring bill management.

`app/bills/page.tsx`

- Manages recurring bills.
- Shows fixed monthly cost, paid/remaining status, due days, auto-log marker,
  and mark-paid actions.

`app/debts/page.tsx`

- Manages debts and IOUs.
- Shows snowball/avalanche ordering, payoff estimate, what-if extra payment
  simulator, progress rings, and quick payments.

`app/insights/page.tsx`

- Manages accounts.
- Shows net worth, account balances, net-worth history, six-month trend,
  spending donut, month-over-month comparison, budget progress, top categories,
  and member split.

`app/advisor/page.tsx`

- Chat UI for Coach.
- Builds the live financial snapshot and calls `/api/advisor`.
- Supports starter prompts and weekly check-in handoff through `sessionStorage`.

`app/settings/page.tsx`

- Household name, currency, theme, pay schedule, reminders, member management,
  sync card, budgets, backup/restore, and reset.

## PWA And Shell

`app/layout.tsx` wraps the app in `StoreProvider`, `AppShell`, and service worker
registration.

`components/AppShell.tsx` owns the common frame, onboarding gate, and bottom
navigation. `components/SwRegister.tsx` registers `public/sw.js`.

The app is designed to be installable and phone-first. Offline behavior is
limited: already loaded assets and local data can be viewed, but AI routes and
sync require network access.

## Known Constraints

- There is no server database unless KV sync is configured.
- Local browser data loss clears the budget unless the user has a backup or
  sync enabled.
- Sync codes are shared secrets and are not authenticated user accounts.
- Merge uses simple last-write/union rules; simultaneous edits to the same
  record can overwrite fields.
- Voice input relies on browser speech recognition and is browser-dependent.
- AI features require `ANTHROPIC_API_KEY`.
- The repository currently contains some emoji/text mojibake in source comments
  and UI strings. Functionality may still work, but text cleanup would improve
  polish.

## Good Next Improvements

High-value product work:

- Add tests for `lib/insights.ts`, `lib/merge.ts`, and store migration.
- Add edit flows for existing transactions, budgets, bills, goals, debts, and
  accounts instead of mostly delete/recreate or prompt-based edits.
- Add explicit recurring income/paycheck support.
- Add better sync setup UX with generated household codes and clearer conflict
  expectations.
- Add import validation/version checks before replacing local data.
- Add category normalization so AI-created and user-created category names do
  not fragment charts.
- Add a real notification/check-in scheduling path for installed PWAs.
- Add accessible labels and replace emoji-only controls where needed.
- Clean up mojibake/encoding issues across README and UI strings.
- Add E2E smoke tests for onboarding, quick capture, bill payment, debt payment,
  backup/restore, and advisor snapshot construction.

Likely first files to touch:

- Data model changes: `lib/types.ts`, then `lib/store.tsx`, `lib/merge.ts`,
  affected screens, and backup/import compatibility.
- Budget math changes: `lib/insights.ts`, then dashboard/plan/insights screens.
- AI parse changes: `app/api/parse/route.ts`, `app/api/parse-receipt/route.ts`,
  `components/QuickCapture.tsx`, and `ParsedEntry` in `lib/types.ts`.
- Coach behavior changes: `app/api/advisor/route.ts` and snapshot construction
  in `app/advisor/page.tsx`.
- Sync changes: `lib/merge.ts`, `lib/store.tsx`, `app/api/sync/route.ts`,
  `components/SyncCard.tsx`.

