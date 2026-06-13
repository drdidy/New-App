import { NextRequest, NextResponse } from "next/server";
import { getClient, MODELS, hasApiKey } from "@/lib/anthropic";
import { contentLengthOk, rateLimit, requestIp } from "@/lib/rateLimit";
import { parseRequestSchema, parsedResponseSchema } from "@/lib/validation";

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
              "account",
              "bill",
              "budget",
              "goal",
            ],
          },
          amount: { type: "number" },
          category: { type: "string" },
          description: { type: "string" },
          party: { type: "string" },
          apr: { type: "number" },
          accountType: {
            type: "string",
            enum: ["checking", "savings", "cash", "investment", "other"],
          },
          dayOfMonth: { type: "number" },
          monthlyContribution: { type: "number" },
          summary: { type: "string" },
        },
        required: ["kind", "amount", "summary"],
      },
    },
  },
  required: ["entries"],
};

const SYSTEM = `You convert a person's casual, plain-language note about their money into structured entries.

The user is overwhelmed by budgeting and HATES typing, so they speak naturally to set up and update their whole financial picture. Map each thing they say to the right kind:

SPENDING & INCOME
- "spent 40 on gas" -> expense, category Transport
- "groceries 85 and 12 coffee" -> two expenses
- "got paid 2000" / "salary came in" -> income

DEBTS (money owed)
- "I still owe James 200" -> debt_i_owe, party James
- "Sarah owes me 50" -> debt_owed_to_me, party Sarah
- "paid James back 100" / "paid 100 toward my visa" -> debt_payment, party James / Visa
- "I owe 3000 on my visa at 22% apr, minimum 90" -> debt_i_owe, party Visa, amount 3000, apr 22

ACCOUNTS (real money the user HAS — balances)
- "my checking has 1850" / "I have 1850 in checking" -> account, accountType checking, amount 1850, description "Checking"
- "2000 in savings" -> account, accountType savings, amount 2000, description "Savings"
- "400 cash in my wallet" -> account, accountType cash, amount 400, description "Wallet"

RECURRING BILLS (fixed monthly costs with a due day)
- "rent is 1400 due on the 1st" -> bill, amount 1400, category Rent, dayOfMonth 1, description "Rent"
- "netflix 15 a month on the 12th" -> bill, amount 15, category Subscription, dayOfMonth 12, description "Netflix"
- "phone bill 60 on the 20th" -> bill, amount 60, category Phone, dayOfMonth 20, description "Phone"

BUDGETS (a monthly spending cap for a category)
- "budget 300 for dining" / "keep groceries under 500" -> budget, category Dining/Groceries, amount (the cap)

SAVINGS GOALS
- "save for a car, goal 5000, 200 a month" -> goal, description "Car", amount 5000, monthlyContribution 200
- "emergency fund of 6000" -> goal, description "Emergency fund", amount 6000

Rules:
- One note may contain SEVERAL entries of DIFFERENT kinds. Return all of them.
- amount is always a positive number. Infer thousands from "k" (2k -> 2000).
- Distinguish carefully: money the user HAS in an account = account; money they OWE = debt_i_owe; a fixed monthly cost = bill; a spending cap = budget; money set aside toward a target = goal; a one-off purchase = expense.
- For expenses/income/bills/budgets choose a short Title-Case category (Groceries, Transport, Rent, Dining, Utilities, Salary, Subscription, Phone, etc.).
- For debts, "party" is the person or account name, capitalized. For accounts/bills/goals put the name in "description".
- "summary" is a short human confirmation of that single entry, e.g. "Logged $40 expense for gas (Transport)", "Added Checking account ($1,850)", "Added Rent bill ($1,400, due 1st)".
- If the note is not about money at all, return an empty entries array.
- Today's currency is US Dollars. Do not include currency symbols in numbers.`;

export async function POST(req: NextRequest) {
  if (!contentLengthOk(req, 20_000)) {
    return NextResponse.json({ error: "That note is too large." }, { status: 413 });
  }
  const limited = rateLimit(`parse:${requestIp(req)}`, 40, 60_000);
  if (!limited.ok) {
    return NextResponse.json(
      { error: "Too many requests. Try again shortly." },
      { status: 429, headers: { "Retry-After": String(limited.retryAfter) } },
    );
  }

  if (!hasApiKey()) {
    return NextResponse.json(
      { error: "Server is missing ANTHROPIC_API_KEY." },
      { status: 503 },
    );
  }

  let text = "";
  try {
    const body = parseRequestSchema.safeParse(await req.json());
    if (!body.success) {
      return NextResponse.json({ error: "Enter a shorter money note." }, { status: 400 });
    }
    text = body.data.text;
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
    const parsed = parsedResponseSchema.parse(JSON.parse(block?.text || '{"entries":[]}'));
    return NextResponse.json(parsed);
  } catch (err: any) {
    console.error("parse error", err?.message);
    return NextResponse.json(
      { error: "Could not understand that. Try rephrasing." },
      { status: 500 },
    );
  }
}
