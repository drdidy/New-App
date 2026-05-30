import Anthropic from "@anthropic-ai/sdk";

// Hybrid model strategy — picked to keep this personal app cheap to run
// (~$2-5/month at daily use) without sacrificing quality where it matters:
//
//   FAST  (Haiku)  — high-volume, simple extraction: turning a sentence or a
//                    receipt photo into structured entries. Pennies per call.
//   SMART (Sonnet) — the AI Coach's advice/plans: needs real reasoning, but
//                    Sonnet is ~5x cheaper than Opus and more than capable.
//   DEEP  (Opus)   — reserved; not used by default. Available if a feature
//                    ever needs the very deepest reasoning.
export const MODELS = {
  fast: "claude-haiku-4-5-20251001",
  smart: "claude-sonnet-4-6",
  deep: "claude-opus-4-8",
} as const;

// Back-compat default (used anywhere a single model is expected).
export const MODEL = MODELS.smart;

let client: Anthropic | null = null;

// Lazily construct the client at request time (not at module load / build
// time). The API key is read from the environment so it is never shipped to
// the browser. Set ANTHROPIC_API_KEY in your deployment (e.g. Vercel project
// settings) or in a local .env.local file.
export function getClient(): Anthropic {
  if (!client) {
    client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  }
  return client;
}

export function hasApiKey(): boolean {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}
