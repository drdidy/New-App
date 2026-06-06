# Money Coach

Money Coach is a private, phone-first budgeting and debt coaching PWA for households. It is designed for people who do not want to become spreadsheet experts just to understand what they can safely spend today.

The app centers on a novice-friendly financial cockpit:

- **Today** - a clear daily command center with safe-to-spend, bills left, debt owed, recent activity, and the next best action.
- **Quick capture** - type, speak, or photograph what happened and Money Coach converts it into structured income, expense, debt, and receipt entries.
- **Receipt line items** - receipt photos can capture readable items, amounts, quantities, and practical grocery categories so spending can be reviewed below the store-total level.
- **Plan** - monthly budget, goals, pay-cycle pacing, and account balances.
- **Spending** - category breakdowns, month-over-month trends, budget status, and household/member splits.
- **Debt** - payoff planning with snowball, avalanche, and hybrid strategy guidance.
- **Coach** - AI planning help that can explain trade-offs, suggest debt reduction moves, and provide practical money advice based on the household snapshot.
- **PWA install** - works as an installable mobile app with professional app icons and offline viewing.

## Tech

- **Next.js 15 App Router + React + TypeScript**
- **Claude API** (`@anthropic-ai/sdk`) for sentence parsing, receipt vision, and coaching. API calls run server-side so the key never reaches the browser.
- **Local-first storage** in browser `localStorage`, with optional encrypted household sync through Vercel KV / Upstash-compatible REST env vars.
- **Installable PWA** with manifest, service worker, and Android/iOS home-screen assets.

## Run It Locally

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

4. Open http://localhost:3000 on your computer or on a phone connected to the same Wi-Fi.

## Environment Variables

Required for AI features:

- `ANTHROPIC_API_KEY`

Optional for cross-device sync:

- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`
- `SYNC_KEY_SECRET` - at least 32 characters

## Privacy And Sync

Money Coach is local-first. The household budget is stored in the current browser by default. AI features send only the note, receipt image, or Coach snapshot the user chooses to analyze to the server-side API route. Optional sync stores a shared household blob when the KV sync variables are configured.

Money Coach provides educational planning help only. It cannot move money, access bank accounts, negotiate with creditors, or replace a licensed financial professional.

## API Routes

| Endpoint | Purpose |
| --- | --- |
| `POST /api/parse` | Converts a plain-language money note into structured app entries. |
| `POST /api/parse-receipt` | Reads a receipt image and returns a store, total, category, and line items when visible. |
| `POST /api/advisor` | Sends a compact financial snapshot and chat history for personalized planning advice. |
| `GET/POST /api/sync/[code]` | Optional encrypted household sync when KV env vars are configured. |

## Production Checks

Use the built-in QA script before deploy:

```bash
npm run qa
```

It runs linting, TypeScript, tests, and a production build.
