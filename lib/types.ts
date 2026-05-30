// Core data model for Money Coach.
// Stored locally on-device (localStorage). Designed as a household app for up
// to a couple of people (e.g. you + your partner): everything can be attributed
// to a member, and the dashboard rolls up a shared household view plus a
// per-person split.

export type TxnType = "expense" | "income";

// A household member. Two-person households are the common case, but the model
// supports more. Each member gets a colour + emoji used for avatars/charts.
export interface Member {
  id: string;
  name: string;
  emoji: string; // avatar glyph, e.g. "🦊"
  color: string; // accent hue used in charts/avatars, e.g. "#5fe0a6"
  monthlyIncome?: number; // optional self-reported baseline
}

export interface Transaction {
  id: string;
  type: TxnType;
  amount: number; // always positive; `type` carries the direction
  category: string; // e.g. "Groceries", "Salary", "Rent"
  description: string;
  date: string; // ISO date (YYYY-MM-DD)
  memberId?: string; // who this belongs to
  createdAt: number; // epoch ms
}

// A debt is money owed *by* the household (a liability) or *to* the household
// (someone owes them). We track both so the dashboard shows a true net picture.
export type DebtDirection = "i_owe" | "owed_to_me";

export interface Debt {
  id: string;
  direction: DebtDirection;
  party: string; // who you owe / who owes you (e.g. "James", "Visa card")
  balance: number; // remaining amount, positive
  original?: number; // starting balance, for payoff progress
  apr?: number; // annual interest rate %, optional (for payoff planning)
  minPayment?: number; // minimum monthly payment, optional
  dueDate?: string; // ISO date of next payment, optional
  memberId?: string; // whose debt (optional; defaults to household)
  note?: string;
  createdAt: number;
}

// A monthly spending limit for a category. Drives budget progress + alerts.
export interface Budget {
  category: string;
  limit: number; // monthly cap
}

export type ThemeName = "dark" | "light";

export interface AppData {
  version: number;
  onboarded: boolean;
  householdName?: string;
  members: Member[];
  transactions: Transaction[];
  debts: Debt[];
  budgets: Budget[];
  currency: string; // ISO code, e.g. "USD"
  theme: ThemeName;
  monthlyIncome?: number; // legacy/global fallback
}

// The shape returned by /api/parse: normalized entries extracted from a single
// natural-language note. One note can yield several entries.
export type ParsedKind =
  | "expense"
  | "income"
  | "debt_i_owe"
  | "debt_owed_to_me"
  | "debt_payment";

export interface ParsedEntry {
  kind: ParsedKind;
  amount: number;
  category?: string;
  description?: string;
  party?: string;
  apr?: number;
  summary: string;
}
