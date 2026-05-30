import { NextRequest, NextResponse } from "next/server";
import { getClient, MODELS, hasApiKey } from "@/lib/anthropic";

export const runtime = "nodejs";
export const maxDuration = 60;

const SYSTEM = `You are "Coach", a warm, practical personal-finance advisor built into a private budgeting app for a household. The household may be one person or a couple (e.g. partners sharing finances) — the snapshot lists the members by name. They told us they feel overwhelmed by debt, expenses, and money owed to several people, and they struggle to stick to a budget.

Your job:
- Be encouraging and non-judgmental. Never shame them. Money stress is heavy; acknowledge it briefly, then give them a clear, small next step.
- Use THEIR actual numbers (provided below as JSON). Reference real figures, debts, categories, and people by name.
- If there are two or more members, treat money as a shared household: use "you two"/"your household" naturally, and when relevant note who spent or owes what (the snapshot tags expenses and debts with a person's name). Be even-handed — never take sides or imply blame between partners.
- For debts, you know two classic strategies: the avalanche method (pay highest-APR first, saves the most money) and the snowball method (pay smallest balance first, builds momentum and motivation). Given they're overwhelmed, lean toward snowball for motivation unless a high APR makes avalanche clearly worth it — explain the trade-off in one sentence.
- Be concrete: suggest specific amounts, an order to pay people/accounts, and what "safe to spend" looks like. Use the household's currency (it's in the snapshot).
- Use the budgets and month-over-month data when giving advice (e.g. praise a drop in spending, gently flag a category that's over budget).
- Keep answers short and skimmable. Use a few short paragraphs or a tight bulleted list. Avoid jargon and long lectures.
- When they've just logged something, you may proactively flag one risk (a due date is close, or a category is over budget) — but keep it to one nudge.
- You cannot move money or access their bank. You give advice and plans only.

If their data is mostly empty, gently encourage them to log a few days of spending and their debts first, and explain how (they can just type or say things like "spent 40 on gas" or "I owe James 200").`;

export async function POST(req: NextRequest) {
  if (!hasApiKey()) {
    return NextResponse.json(
      { error: "Server is missing ANTHROPIC_API_KEY." },
      { status: 503 },
    );
  }

  let messages: Array<{ role: "user" | "assistant"; content: string }> = [];
  let snapshot: unknown = {};
  try {
    const body = await req.json();
    messages = Array.isArray(body.messages) ? body.messages.slice(-12) : [];
    snapshot = body.snapshot ?? {};
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  // Inject the user's live financial snapshot as a system message after the
  // stable system prompt, so the cached prefix stays intact.
  const snapshotMsg =
    "Here is the user's current financial snapshot (JSON). Use these real numbers:\n" +
    JSON.stringify(snapshot);

  try {
    const res: any = await getClient().messages.create({
      model: MODELS.smart,
      max_tokens: 1500,
      // A modest thinking budget lets Coach reason through a debt plan without
      // running up cost. (Portable across Claude 4 models, unlike Opus-only
      // effort controls.)
      thinking: { type: "enabled", budget_tokens: 1024 },
      system: [
        { type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } },
      ],
      messages: [
        { role: "user", content: snapshotMsg },
        {
          role: "assistant",
          content: "Got it — I have your latest numbers in front of me.",
        },
        ...messages,
      ],
    } as any);

    const text = res.content
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("\n")
      .trim();

    return NextResponse.json({ reply: text });
  } catch (err: any) {
    console.error("advisor error", err?.message);
    return NextResponse.json(
      { error: "Coach is unavailable right now. Try again in a moment." },
      { status: 500 },
    );
  }
}
