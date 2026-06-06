const buckets = new Map<string, { count: number; resetAt: number }>();
const MAX_BUCKETS = 10_000;

export function rateLimit(
  key: string,
  limit: number,
  windowMs: number,
): { ok: boolean; retryAfter: number } {
  const now = Date.now();
  if (buckets.size > MAX_BUCKETS) {
    for (const [bucketKey, bucket] of buckets) {
      if (bucket.resetAt <= now) buckets.delete(bucketKey);
    }
  }
  const current = buckets.get(key);
  if (!current || current.resetAt <= now) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true, retryAfter: 0 };
  }
  if (current.count >= limit) {
    return { ok: false, retryAfter: Math.ceil((current.resetAt - now) / 1000) };
  }
  current.count += 1;
  return { ok: true, retryAfter: 0 };
}

export function requestIp(req: Request): string {
  const realIp = req.headers.get("x-real-ip") || req.headers.get("cf-connecting-ip");
  if (realIp) return realIp.trim();
  const forwarded = req.headers.get("x-forwarded-for");
  return forwarded?.split(",")[0]?.trim() || "local";
}

export function contentLengthOk(req: Request, maxBytes: number): boolean {
  const len = req.headers.get("content-length");
  if (!len) return true;
  const n = Number(len);
  return Number.isFinite(n) && n >= 0 && n <= maxBytes;
}
