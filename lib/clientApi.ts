"use client";

// Client-side helpers for talking to the API safely.
//
// Two problems this solves:
//  1. Platform errors (Vercel 413 "Request Entity Too Large", 504 gateway HTML,
//     empty bodies) are NOT JSON. Calling res.json() on them throws
//     "Unexpected token 'R' ... is not valid JSON". postJson() reads the body as
//     text first and only then tries to parse it, returning a friendly,
//     status-aware error instead of crashing.
//  2. Phone photos are multi-MB; base64 inflates them past Vercel's ~4.5MB body
//     limit. compressImage() downscales + re-encodes to a small JPEG first.

export interface ApiResult<T = unknown> {
  ok: boolean;
  status: number;
  data: T | null;
  error?: string;
}

function messageForStatus(status: number, serverError?: string): string {
  if (serverError) return serverError;
  switch (status) {
    case 0:
      return "Network error — check your connection and try again.";
    case 413:
      return "That was too large. Try a smaller or clearer photo.";
    case 429:
      return "A bit too fast — give it a moment and try again.";
    case 503:
      return "The AI service isn’t set up (missing API key).";
    case 504:
      return "That took too long. Try again.";
    default:
      return "Something went wrong. Please try again.";
  }
}

export async function postJson<T = unknown>(url: string, body: unknown): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return { ok: false, status: 0, data: null, error: messageForStatus(0) };
  }

  const text = await res.text().catch(() => "");
  let data: T | null = null;
  if (text) {
    try {
      data = JSON.parse(text) as T;
    } catch {
      data = null; // non-JSON body (platform error page, etc.)
    }
  }

  if (!res.ok) {
    const serverError = (data as { error?: string } | null)?.error;
    return { ok: false, status: res.status, data, error: messageForStatus(res.status, serverError) };
  }
  return { ok: true, status: res.status, data };
}

// Downscale + re-encode an image file to a compact JPEG data URL so uploads stay
// well under the serverless body limit. Falls back to the raw file if the canvas
// pipeline isn't available (e.g. an unsupported format).
export function compressImage(file: File, maxEdge = 1500, quality = 0.7): Promise<string> {
  return new Promise((resolve) => {
    const fallback = () => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result));
      r.onerror = () => resolve("");
      r.readAsDataURL(file);
    };
    try {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        try {
          const scale = Math.min(1, maxEdge / Math.max(img.width, img.height));
          const w = Math.max(1, Math.round(img.width * scale));
          const h = Math.max(1, Math.round(img.height * scale));
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          if (!ctx) {
            URL.revokeObjectURL(url);
            return fallback();
          }
          ctx.drawImage(img, 0, 0, w, h);
          const out = canvas.toDataURL("image/jpeg", quality);
          URL.revokeObjectURL(url);
          resolve(out && out.length > 32 ? out : "");
        } catch {
          URL.revokeObjectURL(url);
          fallback();
        }
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        fallback();
      };
      img.src = url;
    } catch {
      fallback();
    }
  });
}
