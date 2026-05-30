import { NextRequest, NextResponse } from "next/server";
import { getClient, MODELS, hasApiKey } from "@/lib/anthropic";

export const runtime = "nodejs";

const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    found: { type: "boolean" },
    amount: { type: "number" },
    merchant: { type: "string" },
    category: { type: "string" },
    summary: { type: "string" },
  },
  required: ["found", "amount", "summary"],
};

const SYSTEM = `You read a photo of a receipt, bank transfer, or payment screenshot and extract the single most important expense.

Return:
- found: true if you can see a clear total amount, else false.
- amount: the grand total actually paid (a positive number, no currency symbol).
- merchant: the store / payee name if visible.
- category: a short Title-Case spending category (Groceries, Dining, Transport, Utilities, Shopping, etc.).
- summary: a one-line confirmation, e.g. "Walmart — $42.50 (Groceries)".

If the image is not a receipt or you cannot read a total, set found=false and amount=0.`;

export async function POST(req: NextRequest) {
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

  try {
    const res: any = await getClient().messages.create({
      model: MODELS.fast,
      max_tokens: 512,
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
            { type: "text", text: "Extract the expense from this image." },
          ],
        },
      ],
      output_config: { format: { type: "json_schema", schema: SCHEMA } },
    } as any);

    const block = res.content.find((b: any) => b.type === "text");
    const parsed = JSON.parse(block?.text || '{"found":false,"amount":0}');
    return NextResponse.json(parsed);
  } catch (err: any) {
    console.error("receipt error", err?.message);
    return NextResponse.json(
      { error: "Could not read that image." },
      { status: 500 },
    );
  }
}
