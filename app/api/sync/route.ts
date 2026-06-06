import { NextRequest, NextResponse } from "next/server";
import { kvConfigured, kvGet, kvSet } from "@/lib/kv";
import { mergeData, sanitizeForSync } from "@/lib/merge";
import type { AppData } from "@/lib/types";
import { createHash, createHmac } from "crypto";
import { contentLengthOk, rateLimit, requestIp } from "@/lib/rateLimit";

export const runtime = "nodejs";

const CODE_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MIN_CODE_LEN = 16;

function cleanCode(code: string): string {
  return code.trim().toLowerCase().replace(/[^a-z0-9-]/g, "");
}

function codeValidAfterCleaning(code: string): boolean {
  const clean = cleanCode(code);
  return clean.length >= MIN_CODE_LEN && CODE_RE.test(clean);
}

// Household blobs are stored under a non-reversible key. SYNC_KEY_SECRET makes
// this an HMAC; without it we still avoid directly addressable raw codes.
function keyFor(code: string): string {
  const clean = cleanCode(code);
  const secret = process.env.SYNC_KEY_SECRET;
  const digest = secret
    ? createHmac("sha256", secret).update(clean).digest("hex")
    : createHash("sha256").update(clean).digest("hex");
  return `mc:household:${digest}`;
}

function validCode(code: unknown): code is string {
  return typeof code === "string" && codeValidAfterCleaning(code);
}

export async function POST(req: NextRequest) {
  if (!contentLengthOk(req, 1_000_000)) {
    return NextResponse.json({ ok: false, error: "Request is too large." }, { status: 413 });
  }

  const ip = requestIp(req);
  const limited = rateLimit(`sync:${ip}`, 60, 60_000);
  if (!limited.ok) {
    return NextResponse.json(
      { ok: false, error: "Too many sync attempts. Try again shortly." },
      { status: 429, headers: { "Retry-After": String(limited.retryAfter) } },
    );
  }

  if (!kvConfigured()) {
    return NextResponse.json(
      { ok: false, configured: false, error: "Sync is not set up on the server." },
      { status: 200 },
    );
  }

  let body: any;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Bad request" }, { status: 400 });
  }

  const action = body?.action;

  // Lightweight check used by the UI to show whether sync is available.
  if (action === "status") {
    return NextResponse.json({ ok: true, configured: true });
  }

  if (!validCode(body?.code)) {
    return NextResponse.json(
      { ok: false, error: "Use the full household code from Settings." },
      { status: 400 },
    );
  }
  const key = keyFor(body.code);

  try {
    if (action === "pull") {
      const raw = await kvGet(key);
      const data = raw ? (JSON.parse(raw) as AppData) : null;
      return NextResponse.json({ ok: true, configured: true, data });
    }

    if (action === "push") {
      const incoming = body.data as AppData;
      if (!incoming || typeof incoming !== "object") {
        return NextResponse.json({ ok: false, error: "No data" }, { status: 400 });
      }
      // Merge with whatever is already stored so simultaneous pushes from both
      // phones don't clobber each other.
      const raw = await kvGet(key);
      const existing = raw ? (JSON.parse(raw) as AppData) : null;
      const merged = existing
        ? mergeData(existing, sanitizeForSync(incoming))
        : sanitizeForSync(incoming);
      await kvSet(key, JSON.stringify(merged));
      return NextResponse.json({ ok: true, configured: true, data: merged });
    }

    return NextResponse.json({ ok: false, error: "Unknown action" }, { status: 400 });
  } catch (err: any) {
    console.error("sync error", err?.message);
    return NextResponse.json(
      { ok: false, configured: true, error: "Sync failed. Try again." },
      { status: 500 },
    );
  }
}
