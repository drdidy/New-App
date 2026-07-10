import { NextRequest, NextResponse } from "next/server";
import { getClient, MODELS, hasApiKey } from "@/lib/anthropic";
import { contentLengthOk, rateLimit, requestIp } from "@/lib/rateLimit";
import { receiptResponseSchema } from "@/lib/validation";

export const runtime = "nodejs";

const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    found: { type: "boolean" },
    amount: { type: "number" },
    merchant: { type: "string" },
    category: { type: "string" },
    items: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          name: { type: "string" },
          amount: { type: "number" },
          category: { type: "string" },
          quantity: { type: "number" },
        },
        required: ["name", "amount", "category"],
      },
    },
    summary: { type: "string" },
  },
  required: ["found", "amount", "summary"],
};

const SYSTEM = `You read a photo of a receipt, bank transfer, or payment screenshot and extract the most important expense plus readable line items.

Return:
- found: true if you can see a clear total amount, else false.
- amount: the grand total actually paid (a positive number, no currency symbol).
- merchant: the store / payee name if visible.
- category: a short Title-Case spending category for the overall receipt.
- items: readable line items with name, amount, quantity if visible, and a practical spending category.
- summary: a one-line confirmation, e.g. "Walmart - $42.50 (Groceries)".

For grocery receipts, use helpful line-item categories like Produce, Meat & Seafood, Dairy, Pantry, Snacks, Drinks, Household, Personal Care, Pet, Baby, Alcohol, Prepared Food, Tax/Fee, Other.
If the receipt is long, return the clearest visible items and do not invent unreadable names.
If the image is not a receipt or you cannot read a total, set found=false, amount=0, and items=[].`;

export async function POST(req: NextRequest) {
  if (!contentLengthOk(req, 7_000_000)) {
    return NextResponse.json({ error: "That image is too large." }, { status: 413 });
  }
  const limited = rateLimit(`receipt:${requestIp(req)}`, 12, 60_000);
  if (!limited.ok) {
    return NextResponse.json(
      { error: "Too many receipt scans. Try again shortly." },
      { status: 429, headers: { "Retry-After": String(limited.retryAfter) } },
    );
  }

  if (!hasApiKey()) {
    return NextResponse.json(
      { error: "Server is missing ANTHROPIC_API_KEY." },
      { status: 503 },
    );
  }

  let dataUrl = "";
  try {
    const body = await req.json();
    dataUrl = String(body.image || "");
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  const match = /^data:(image\/(png|jpeg|jpg|webp|gif));base64,(.+)$/.exec(
    dataUrl,
  );
  if (!match) {
    return NextResponse.json(
      { error: "Unsupported image format." },
      { status: 400 },
    );
  }
  const mediaType = match[1] === "image/jpg" ? "image/jpeg" : match[1];
  const base64 = match[3];
  if (base64.length > 6_500_000) {
    return NextResponse.json({ error: "That image is too large." }, { status: 413 });
  }

  try {
    const res: any = await getClient().messages.create({
      model: MODELS.fast,
      max_tokens: 3000,
      thinking: { type: "disabled" },
      system: [
        { type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } },
      ],
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: { type: "base64", media_type: mediaType, data: base64 },
            },
            { type: "text", text: "Extract the total and readable line items from this image." },
          ],
        },
      ],
      output_config: { format: { type: "json_schema", schema: SCHEMA } },
    } as any);

    const block = res.content.find((b: any) => b.type === "text");
    const parsed = receiptResponseSchema.parse(
      JSON.parse(block?.text || '{"found":false,"amount":0,"items":[]}'),
    );
    return NextResponse.json(parsed);
  } catch (err: any) {
    console.error("receipt error", err?.message);
    return NextResponse.json(
      { error: "Could not read that image." },
      { status: 500 },
    );
  }
}
