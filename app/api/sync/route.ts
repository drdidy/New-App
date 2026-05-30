import { NextRequest, NextResponse } from "next/server";
import { kvConfigured, kvGet, kvSet } from "@/lib/kv";
import { mergeData, sanitizeForSync } from "@/lib/merge";
import type { AppData } from "@/lib/types";

export const runtime = "nodejs";

// Household blobs are stored under a namespaced key derived from the user's
// shared code. The code is a shared secret between the two phones.
function keyFor(code: string): string {
  const clean = code.trim().toLowerCase().replace(/[^a-z0-9-]/g, "");
  return `mc:household:${clean}`;
}

function validCode(code: unknown): code is string {
  return typeof code === "string" && code.trim().length >= 4;
}

export async function POST(req: NextRequest) {
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
      { ok: false, error: "A household code of at least 4 characters is required." },
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
