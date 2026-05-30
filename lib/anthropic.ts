import Anthropic from "@anthropic-ai/sdk";

// We default to the most capable model. Parsing is fast even on Opus; the
// advisor benefits from the extra intelligence.
export const MODEL = "claude-opus-4-8";

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
