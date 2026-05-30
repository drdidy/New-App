export function formatMoney(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    maximumFractionDigits: Math.abs(amount) % 1 === 0 ? 0 : 2,
  }).format(amount);
}

// Compact money for tight chart labels: $1.2k, $850.
export function formatMoneyShort(amount: number, currency = "USD"): string {
  const abs = Math.abs(amount);
  if (abs >= 1000) {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(amount);
  }
  return formatMoney(amount, currency);
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

// Friendly relative date, e.g. "Today", "Yesterday", "May 12".
export function friendlyDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diff = Math.round((today.getTime() - d.getTime()) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff > 1 && diff < 7) return `${diff} days ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// "YYYY-MM" for a given date (defaults to now).
export function monthKey(d: Date = new Date()): string {
  return d.toISOString().slice(0, 7);
}

// The "YYYY-MM" of the previous month relative to now.
export function prevMonthKey(d: Date = new Date()): string {
  const x = new Date(d.getFullYear(), d.getMonth() - 1, 1);
  return monthKey(x);
}

// Human month label, e.g. "May".
export function monthLabel(key: string): string {
  const [y, m] = key.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, { month: "long" });
}

// Initials from a name, for avatars when no emoji.
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function clampPct(n: number): number {
  return Math.max(0, Math.min(100, n));
}

// Days until an ISO date (negative if past).
export function daysUntil(iso: string): number {
  const d = new Date(iso + "T00:00:00").getTime();
  const now = Date.now();
  return Math.ceil((d - now) / 86400000);
}

// A small, friendly currency menu for onboarding/settings.
export const CURRENCIES: { code: string; label: string }[] = [
  { code: "USD", label: "US Dollar ($)" },
  { code: "EUR", label: "Euro (€)" },
  { code: "GBP", label: "British Pound (£)" },
  { code: "NGN", label: "Nigerian Naira (₦)" },
  { code: "CAD", label: "Canadian Dollar ($)" },
  { code: "AUD", label: "Australian Dollar ($)" },
  { code: "INR", label: "Indian Rupee (₹)" },
  { code: "ZAR", label: "South African Rand (R)" },
  { code: "KES", label: "Kenyan Shilling (Sh)" },
  { code: "GHS", label: "Ghanaian Cedi (₵)" },
  { code: "JPY", label: "Japanese Yen (¥)" },
];

// Palette + emoji pool for new members.
export const MEMBER_COLORS = [
  "#c2663f",
  "#2e8b72",
  "#7c6ba8",
  "#5e7fa6",
  "#bc5446",
  "#a8743f",
];
export const MEMBER_EMOJIS = ["🦊", "🐧", "🐻", "🦉", "🐬", "🦁", "🐨", "🦄"];
