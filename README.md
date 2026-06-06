# Money Coach 💰

A private, AI-powered budgeting and debt coach — built as a phone-first
**Progressive Web App (PWA)**. It's designed around one problem: *logging money
is usually too tedious to keep up*. So here you don't fill in forms — you just
**talk to it**.

- 🗣️ **Quick capture** — type or speak *"spent 40 on gas and I still owe James 200"*
  and Claude turns it into the right expense + debt entries. No forms.
- 📷 **Snap a receipt** — photo → Claude reads the total and files it.
- 👫 **Household / two-person** — set up you + your partner; attribute spending
  and debts to each person and see a combined view plus a per-person split.
- 📊 **Insights** — animated donut of where money went, this-month-vs-last,
  budget progress with over-limit warnings, top categories, and who-spent-what.
- 🤝 **Debts & IOUs** — track what you owe and what's owed to you, with payoff
  progress rings and a snowball/avalanche plan with an estimated debt-free date.
- 💬 **AI Coach** — sees your household's real numbers (members, budgets,
  trends) and gives an even-handed debt-payoff plan, advice, and gentle nudges.
- ⚙️ **Settings** — manage members, monthly budgets, currency, a light/dark
  theme, and back up / restore your data as a file.
- 🎬 **Crafted UI** — onboarding flow, animated aurora background, glassmorphism,
  count-up balances, confetti + haptics on logging, charts, and spring motion
  (respects reduced-motion).
- 🔒 **Private** — your financial data lives only on your device (browser
  localStorage). No account, no server database.

## Tech

- **Next.js (App Router) + React + TypeScript**
- **Claude API** (`@anthropic-ai/sdk`) for parsing, receipt vision, and advice —
  all server-side so your API key never reaches the browser. Uses a **hybrid
  model strategy** to stay cheap (~$2–5/month at daily use): **Haiku** for the
  high-volume sentence/receipt parsing and **Sonnet** for the AI Coach's advice.
  See `lib/anthropic.ts`.
- Installable PWA (manifest + service worker) — works offline for viewing.

## Run it locally

1. Install dependencies:
   ```bash
   npm install
   ```
2. Add your Anthropic API key:
   ```bash
   cp .env.local.example .env.local
   # then edit .env.local and paste your key
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:3000 on your computer, or on your phone (same Wi-Fi)
   via your computer's local IP.

## Put it on your phone's home screen

Deploy it (e.g. to **Vercel** — set `ANTHROPIC_API_KEY` in the project's
Environment Variables), open the URL on your phone, then:

- **iPhone (Safari):** Share → *Add to Home Screen*
- **Android (Chrome):** ⋮ menu → *Install app* / *Add to Home Screen*

It'll open like a native app, full-screen, with its own icon.

## Privacy and sync

Money Coach is local-first: the household budget is stored in this browser by
default. AI features send only the note, receipt image, or Coach snapshot you
choose to analyze to the server-side Claude API. Optional cross-device sync
stores a shared household blob in KV when `KV_REST_API_URL`,
`KV_REST_API_TOKEN`, and a 32+ character `SYNC_KEY_SECRET` are configured.

Money Coach provides educational planning help only. It cannot move money,
access bank accounts, or replace a licensed financial professional.

## How the AI works

| Endpoint | What it does |
| --- | --- |
| `POST /api/parse` | Turns a plain sentence into structured expense/income/debt entries (JSON-schema-constrained). |
| `POST /api/parse-receipt` | Reads a receipt photo (Claude vision) → one expense. |
| `POST /api/advisor` | Sends your live financial snapshot + chat history → personalized advice. |

## Notes

- Voice input uses the browser's built-in speech recognition (best on Chrome /
  Android; Safari support varies).
- Because data is stored per-device, clearing your browser data clears the app.
  A cloud-sync option could be added later.
