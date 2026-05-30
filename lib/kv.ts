// Tiny server-only client for Upstash Redis / Vercel KV over its REST API.
// Uses plain fetch so we don't add a dependency. Configured automatically when
// you add a KV/Upstash integration to the Vercel project (it injects
// KV_REST_API_URL + KV_REST_API_TOKEN). If those are absent, sync is simply
// "not configured" and the app stays fully local.

const URL_ENV = process.env.KV_REST_API_URL;
const TOKEN_ENV = process.env.KV_REST_API_TOKEN;

export function kvConfigured(): boolean {
  return Boolean(URL_ENV && TOKEN_ENV);
}

async function command(args: (string | number)[]): Promise<any> {
  if (!kvConfigured()) throw new Error("KV not configured");
  const res = await fetch(URL_ENV as string, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN_ENV}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(args),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`KV error ${res.status}`);
  }
  const json = await res.json();
  return json.result;
}

export async function kvGet(key: string): Promise<string | null> {
  return (await command(["GET", key])) ?? null;
}

export async function kvSet(key: string, value: string): Promise<void> {
  // Expire after ~2 years of inactivity so abandoned households don't linger.
  await command(["SET", key, value, "EX", 63072000]);
}
