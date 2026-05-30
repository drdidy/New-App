// Core data model for Money Coach.
// Everything is stored locally on the user's device (localStorage) — this app
// is single-user and private by design, so there is no server database.

export type TxnType = "expense" | "income";

export interface Transaction {
  id: string;
  type: TxnType;
  amount: number; // always positive; `type` carries the direction
  category: string; // e.g. "Groceries", "Salary", "Rent"
  description: string;
  date: string; // ISO date (YYYY-MM-DD)
  createdAt: number; // epoch ms
}

// A debt is money owed *by* the user (a liability) or *to* the user (someone
// owes them). We track both so the dashboard can show a true net picture.
export type DebtDirection = "i_owe" | "owed_to_me";

export interface Debt {
  id: string;
  direction: DebtDirection;
  party: string; // who you owe, or who owes you (e.g. "James", "Visa card")
  balance: number; // remaining amount, positive
  apr?: number; // annual interest rate %, optional (for payoff planning)
  minPayment?: number; // minimum monthly payment, optional
  dueDate?: string; // ISO date of next payment, optional
  note?: string;
  createdAt: number;
}

export interface AppData {
  transactions: Transaction[];
  debts: Debt[];
  monthlyIncome?: number; // optional self-reported baseline income
  currency: string; // ISO code, e.g. "USD"
}

// The shape returned by the /api/parse endpoint: a list of normalized entries
// extracted from a single natural-language sentence. One sentence can yield
// several entries ("paid 40 for gas and still owe James 200").
export type ParsedKind =
  | "expense"
  | "income"
  | "debt_i_owe"
  | "debt_owed_to_me"
  | "debt_payment";

export interface ParsedEntry {
  kind: ParsedKind;
  amount: number;
  // expense/income
  category?: string;
  description?: string;
  // debt-related
  party?: string;
  apr?: number;
  // human-readable confirmation of what was understood
  summary: string;
}
