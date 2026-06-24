import { z } from "zod";

const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional();
const money = z.number().finite().nonnegative().max(1_000_000_000);
const timestamp = z.number().finite().nonnegative().optional();
const shortText = (max = 160) => z.string().trim().max(max);

export const receiptLineItemSchema = z.object({
  name: shortText(100),
  amount: money,
  category: shortText(60).default("Other"),
  quantity: z.number().finite().positive().max(100_000).optional(),
});

export const parsedEntrySchema = z.object({
  kind: z.enum([
    "expense", "income", "debt_i_owe", "debt_owed_to_me", "debt_payment",
    "account", "bill", "budget", "goal",
  ]),
  amount: money,
  category: shortText(60).optional(),
  description: shortText(180).optional(),
  party: shortText(120).optional(),
  apr: z.number().finite().min(0).max(300).optional(),
  accountType: z.enum(["checking", "savings", "cash", "investment", "other"]).optional(),
  dayOfMonth: z.number().int().min(1).max(31).optional(),
  monthlyContribution: money.optional(),
  summary: shortText(240),
});

export const parseRequestSchema = z.object({
  text: z.string().trim().min(1).max(1000),
});

export const parsedResponseSchema = z.object({
  entries: z.array(parsedEntrySchema).max(20).default([]),
});

export const receiptResponseSchema = z.object({
  found: z.boolean(),
  amount: money,
  merchant: shortText(120).optional(),
  category: shortText(60).optional(),
  items: z.array(receiptLineItemSchema).max(100).default([]),
  summary: shortText(240).default("Receipt scanned"),
});

const memberSchema = z.object({
  id: shortText(80),
  name: shortText(80),
  emoji: shortText(20).default(""),
  color: shortText(40).default("#8dbbff"),
  monthlyIncome: money.optional(),
  updatedAt: timestamp,
});

const transactionSchema = z.object({
  id: shortText(80),
  type: z.enum(["expense", "income"]),
  amount: money,
  category: shortText(80),
  description: shortText(240).default(""),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  memberId: shortText(80).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
  lineItems: z.array(receiptLineItemSchema).max(100).optional(),
});

const debtPaymentSchema = z.object({
  id: shortText(80),
  amount: money,
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  note: shortText(240).optional(),
  createdAt: z.number().finite().nonnegative(),
});

const debtSchema = z.object({
  id: shortText(80),
  direction: z.enum(["i_owe", "owed_to_me"]),
  kind: z.enum(["person", "card", "loan", "bnpl", "other"]).optional(),
  party: shortText(120),
  balance: money,
  original: money.optional(),
  apr: z.number().finite().min(0).max(300).optional(),
  minPayment: money.optional(),
  dueDate: isoDate,
  paymentDay: z.number().int().min(1).max(31).optional(),
  autoPay: z.boolean().optional(),
  lastPaidMonth: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  memberId: shortText(80).optional(),
  note: shortText(500).optional(),
  payments: z.array(debtPaymentSchema).max(2000).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const budgetSchema = z.object({
  category: shortText(80),
  limit: money,
  updatedAt: timestamp,
});

const goalSchema = z.object({
  id: shortText(80),
  name: shortText(120),
  emoji: shortText(20).default(""),
  color: shortText(40).default("#8dbbff"),
  target: money,
  saved: money,
  monthlyContribution: money.optional(),
  memberId: shortText(80).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const billSchema = z.object({
  id: shortText(80),
  name: shortText(120),
  amount: money,
  category: shortText(80),
  dayOfMonth: z.number().int().min(1).max(31),
  memberId: shortText(80).optional(),
  autoLog: z.boolean().optional(),
  lastPaidMonth: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const recurringIncomeSchema = z.object({
  id: shortText(80),
  name: shortText(120),
  amount: money,
  dayOfMonth: z.number().int().min(1).max(31),
  memberId: shortText(80).optional(),
  autoLog: z.boolean().optional(),
  lastPaidMonth: z.string().regex(/^\d{4}-\d{2}$/).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const bucketSchema = z.object({
  id: shortText(80),
  name: shortText(120),
  emoji: shortText(20).default(""),
  color: shortText(40).default("#14b8a6"),
  kind: z.enum(["save", "invest", "give", "spend", "other"]).default("save"),
  allocType: z.enum(["percent", "fixed"]).optional(),
  allocValue: z.number().finite().nonnegative().max(1_000_000_000).optional(),
  balance: z.number().finite().min(-1_000_000_000).max(1_000_000_000),
  target: money.optional(),
  memberId: shortText(80).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const accountSchema = z.object({
  id: shortText(80),
  name: shortText(120),
  type: z.enum(["checking", "savings", "cash", "investment", "other"]),
  balance: z.number().finite().min(-1_000_000_000).max(1_000_000_000),
  emoji: shortText(20).default(""),
  color: shortText(40).default("#8dbbff"),
  memberId: shortText(80).optional(),
  createdAt: z.number().finite().nonnegative(),
  updatedAt: timestamp,
});

const payCycleSchema = z.object({
  type: z.enum(["monthly", "semimonthly", "biweekly", "weekly"]),
  anchor: isoDate,
});

export const appDataInputSchema = z
  .object({
    version: z.number().int().positive().optional(),
    onboarded: z.boolean().optional(),
    householdName: shortText(120).optional(),
    members: z.array(memberSchema).max(12).optional(),
    transactions: z.array(transactionSchema).max(20_000).optional(),
    debts: z.array(debtSchema).max(2000).optional(),
    budgets: z.array(budgetSchema).max(500).optional(),
    recurringBills: z.array(billSchema).max(1000).optional(),
    recurringIncome: z.array(recurringIncomeSchema).max(500).optional(),
    buckets: z.array(bucketSchema).max(500).optional(),
    goals: z.array(goalSchema).max(1000).optional(),
    accounts: z.array(accountSchema).max(1000).optional(),
    netWorthHistory: z
      .array(
        z.object({
          month: z.string().regex(/^\d{4}-\d{2}$/),
          value: z.number().finite().min(-1_000_000_000).max(1_000_000_000),
        }),
      )
      .max(1200)
      .optional(),
    payCycle: payCycleSchema.optional(),
    currency: z.string().trim().min(3).max(8).optional(),
    theme: z.enum(["dark", "light"]).optional(),
    monthlyIncome: money.optional(),
    remindersEnabled: z.boolean().optional(),
    lastCheckIn: timestamp,
    tombstones: z.array(shortText(120)).max(50_000).optional(),
    settingsUpdatedAt: timestamp,
    syncCode: shortText(200).optional(),
    syncEnabled: z.boolean().optional(),
  })
  .passthrough();

export function parseAppDataInput(value: unknown): Record<string, unknown> | null {
  const parsed = appDataInputSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}
