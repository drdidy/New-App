import { NextRequest, NextResponse } from "next/server";
import { getClient, MODELS, hasApiKey } from "@/lib/anthropic";

export const runtime = "nodejs";

// JSON schema constraining Claude's output to a list of normalized entries.
const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    entries: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          kind: {
            type: "string",
            enum: [
              "expense",
              "income",
              "debt_i_owe",
              "debt_owed_to_me",
              "debt_payment",
            ],
          },
          amount: { type: "number" },
          category: { type: "string" },
          description: { type: "string" },
          party: { type: "string" },
          apr: { type: "number" },
          summary: { type: "string" },
        },
        required: ["kind", "amount", "summary"],
      },
    },
  },
  required: ["entries"],
};

const SYSTEM = `You convert a person's casual, plain-language note about their money into structured entries.

The user is overwhelmed by budgeting, so they will speak naturally and briefly, e.g.:
- "spent 40 on gas" -> one expense, category Transport
- "groceries 85 and 12 coffee" -> two expenses
- "got paid 2000" / "salary came in" -> income
- "I still owe James 200" -> debt_i_owe, party James
- "Sarah owes me 50" -> debt_owed_to_me, party Sarah
- "paid James back 100" / "paid 100 toward my visa" -> debt_payment, party James / Visa

Rules:
- One note may contain SEVERAL entries. Return all of them.
- amount is always a positive number. Infer thousands from "k" (2k -> 2000).
- Choose a short, sensible Title-Case category for expenses/income (Groceries, Transport, Rent, Dining, Utilities, Salary, etc.).
- For debts, "party" is the person or account name, capitalized.
- "summary" is a short human-readable confirmation of that single entry, e.g. "Logged $40 expense for gas (Transport)".
- If the note is not about money at all, return an empty entries array.
- Today's currency is US Dollars. Do not include currency symbols in numbers.`;

export async function POST(req: NextRequest) {
  if (!hasApiKey()) {
    return NextResponse.json(
      { error: "Server is missing ANTHROPIC_API_KEY." },
      { status: 503 },
    );
  }

  let text = "";
  try {
    const body = await req.json();
    text = String(body.text || "").slice(0, 1000);
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
  if (!text.trim()) {
    return NextResponse.json({ entries: [] });
  }

  try {
    const res: any = await getClient().messages.create({
      model: MODELS.fast,
      max_tokens: 1024,
      thinking: { type: "disabled" },
      system: [
        { type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } },
      ],
      messages: [{ role: "user", content: text }],
      output_config: { format: { type: "json_schema", schema: SCHEMA } },
    } as any);

    const block = res.content.find((b: any) => b.type === "text");
    const parsed = JSON.parse(block?.text || '{"entries":[]}');
    return NextResponse.json(parsed);
  } catch (err: any) {
    console.error("parse error", err?.message);
    return NextResponse.json(
      { error: "Could not understand that. Try rephrasing." },
      { status: 500 },
    );
  }
}
