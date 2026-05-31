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

// A savings goal / pot (emergency fund, holiday, new laptop…). `saved` grows as
// the household contributes; `monthlyContribution` is the planned amount that
// the money-plan allocates each month.
export interface Goal {
  id: string;
  name: string;
  emoji: string;
  color: string;
  target: number;
  saved: number;
  monthlyContribution?: number;
  memberId?: string;
  createdAt: number;
}

// A constant, recurring monthly bill (rent, utilities, subscriptions, etc.).
// These are "committed" money: until paid for the month they're subtracted from
// safe-to-spend, and when paid they become a normal expense transaction.
export interface RecurringBill {
  id: string;
  name: string; // e.g. "Rent", "Netflix"
  amount: number;
  category: string; // e.g. "Rent", "Utilities", "Subscription"
  dayOfMonth: number; // 1-31, when it's due
  memberId?: string; // who it belongs to
  autoLog?: boolean; // log it automatically on/after the due day
  lastPaidMonth?: string; // "YYYY-MM" it was last paid/logged for
  createdAt: number;
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
  recurringBills: RecurringBill[];
  goals: Goal[];
  currency: string; // ISO code, e.g. "USD"
  theme: ThemeName;
  monthlyIncome?: number; // legacy/global fallback

  // --- multi-device sync (optional) ---
  // Deleted item ids / budget categories, so deletions propagate across phones
  // instead of reappearing on the next merge.
  tombstones?: string[];
  // Bumped whenever a *scalar* setting (currency/theme/name) changes, so the
  // most recent wins during a merge.
  settingsUpdatedAt?: number;
  // Local-only: the shared household code + whether sync is on. These are never
  // written into the shared cloud blob.
  syncCode?: string;
  syncEnabled?: boolean;
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
