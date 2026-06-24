"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  Account,
  AppData,
  Bucket,
  Budget,
  Debt,
  Goal,
  Member,
  PayCycle,
  RecurringBill,
  RecurringIncome,
  ThemeName,
  Transaction,
  ParsedEntry,
} from "./types";
import { uid, todayISO, monthKey } from "./format";
import { inferDebtKind } from "./insights";
import { mergeData, sanitizeForSync } from "./merge";
import { parseAppDataInput } from "./validation";

const STORAGE_KEY = "money-coach-data-v1";
const CURRENT_VERSION = 2;

export type SyncState = "idle" | "syncing" | "ok" | "error" | "unconfigured";

function freshData(): AppData {
  return {
    version: CURRENT_VERSION,
    onboarded: false,
    householdName: "",
    members: [],
    transactions: [],
    debts: [],
    budgets: [],
    recurringBills: [],
    recurringIncome: [],
    buckets: [],
    goals: [],
    accounts: [],
    netWorthHistory: [],
    payCycle: { type: "monthly" },
    currency: "USD",
    theme: "light",
    tombstones: [],
    settingsUpdatedAt: 0,
    syncEnabled: false,
  };
}

function touch<T extends { createdAt?: number; updatedAt?: number }>(x: T, now = Date.now()): T {
  return { ...x, updatedAt: now };
}

// Bring any older/partial saved blob up to the current shape so upgrades never
// wipe a user's data.
function migrate(raw: any): AppData {
  const base = freshData();
  if (!raw || typeof raw !== "object") return base;
  const now = Date.now();

  const members: Member[] = (Array.isArray(raw.members) ? raw.members : []).map((m: Member) => ({
    ...m,
    updatedAt: m.updatedAt || raw.settingsUpdatedAt || now,
  }));
  // v1 had no members — create a default one and attribute existing items to it.
  let defaultMemberId: string | undefined;
  if (members.length === 0) {
    defaultMemberId = uid();
    members.push({
      id: defaultMemberId,
      name: "You",
      emoji: "🦊",
      color: "#8dbbff",
      monthlyIncome: raw.monthlyIncome,
      updatedAt: now,
    });
  }

  const attribute = <T extends { memberId?: string }>(x: T): T =>
    x.memberId ? x : { ...x, memberId: members[0]?.id };

  // Defensive coercion: a single malformed record (e.g. a non-string `date` or
  // NaN `balance`) must never crash every selector or render "$NaN". We sanitize
  // on the way in so the rest of the app can trust the shapes.
  const num = (v: unknown, fallback = 0): number =>
    typeof v === "number" && Number.isFinite(v) ? v : fallback;
  const safeDate = (v: unknown): string =>
    typeof v === "string" && /^\d{4}-\d{2}-\d{2}/.test(v) ? v.slice(0, 10) : todayISO();

  const transactions: Transaction[] = (Array.isArray(raw.transactions) ? raw.transactions : [])
    .filter((t: any) => t && typeof t === "object")
    .map((t: Transaction) => ({
      ...touch(attribute(t), t.updatedAt || t.createdAt || now),
      type: t.type === "income" ? "income" : "expense",
      amount: Math.abs(num(t.amount)),
      category: typeof t.category === "string" && t.category ? t.category : "Other",
      date: safeDate(t.date),
    }));
  const debts: Debt[] = (Array.isArray(raw.debts) ? raw.debts : [])
    .filter((d: any) => d && typeof d === "object")
    .map((d: Debt) => ({
      ...touch(attribute(d), d.updatedAt || d.createdAt || now),
      balance: Math.max(0, num(d.balance)),
      original: num(d.original ?? d.balance),
      apr: d.apr != null ? num(d.apr) : undefined,
      minPayment: d.minPayment != null ? num(d.minPayment) : undefined,
      direction: d.direction === "owed_to_me" ? "owed_to_me" : "i_owe",
      party: typeof d.party === "string" && d.party ? d.party : "Someone",
      kind: d.kind ?? inferDebtKind(d),
      payments: Array.isArray(d.payments) ? d.payments : [],
    }));
  const recurringBills: RecurringBill[] = (Array.isArray(raw.recurringBills) ? raw.recurringBills : [])
    .filter((b: any) => b && typeof b === "object")
    .map((b: RecurringBill) => ({
      ...touch(attribute(b), b.updatedAt || b.createdAt || now),
      amount: Math.abs(num(b.amount)),
      dayOfMonth: Math.min(31, Math.max(1, Math.round(num(b.dayOfMonth, 1)))),
      category: typeof b.category === "string" && b.category ? b.category : "Other",
    }));
  const goals: Goal[] = (Array.isArray(raw.goals) ? raw.goals : [])
    .filter((g: any) => g && typeof g === "object")
    .map((g: Goal) => ({
      ...touch(attribute(g), g.updatedAt || g.createdAt || now),
      target: Math.max(0, num(g.target)),
      saved: Math.max(0, num(g.saved)),
      monthlyContribution: g.monthlyContribution != null ? Math.max(0, num(g.monthlyContribution)) : undefined,
    }));
  const recurringIncome: RecurringIncome[] = (Array.isArray(raw.recurringIncome) ? raw.recurringIncome : [])
    .filter((x: any) => x && typeof x === "object")
    .map((x: RecurringIncome) => ({
      ...touch(attribute(x), x.updatedAt || x.createdAt || now),
      amount: Math.abs(num(x.amount)),
      dayOfMonth: Math.min(31, Math.max(1, Math.round(num(x.dayOfMonth, 1)))),
      name: typeof x.name === "string" && x.name ? x.name : "Income",
    }));
  const buckets: Bucket[] = (Array.isArray(raw.buckets) ? raw.buckets : [])
    .filter((x: any) => x && typeof x === "object")
    .map((x: Bucket) => ({
      ...touch(attribute(x), x.updatedAt || x.createdAt || now),
      balance: num(x.balance),
      target: x.target != null ? Math.max(0, num(x.target)) : undefined,
      allocValue: x.allocValue != null ? Math.max(0, num(x.allocValue)) : undefined,
      kind: (["save", "invest", "give", "spend", "other"] as const).includes(x.kind) ? x.kind : "save",
      name: typeof x.name === "string" && x.name ? x.name : "Bucket",
    }));
  const accounts: Account[] = (Array.isArray(raw.accounts) ? raw.accounts : [])
    .filter((a: any) => a && typeof a === "object")
    .map((a: Account) => ({
      ...touch(attribute(a), a.updatedAt || a.createdAt || now),
      balance: num(a.balance),
    }));

  const hadData = transactions.length > 0 || debts.length > 0;

  return {
    ...base,
    version: CURRENT_VERSION,
    // If they already had data, don't force them through onboarding.
    onboarded: raw.onboarded ?? hadData,
    householdName: raw.householdName ?? "",
    members,
    transactions,
    debts,
    budgets: Array.isArray(raw.budgets)
      ? raw.budgets
          .filter((b: any) => b && typeof b === "object" && typeof b.category === "string")
          .map((b: Budget) => ({
            category: b.category,
            limit: Math.max(0, num(b.limit)),
            updatedAt: b.updatedAt || raw.settingsUpdatedAt || now,
          }))
      : [],
    recurringBills,
    recurringIncome,
    buckets,
    goals,
    accounts,
    netWorthHistory: Array.isArray(raw.netWorthHistory) ? raw.netWorthHistory : [],
    payCycle: raw.payCycle && raw.payCycle.type ? raw.payCycle : { type: "monthly" },
    currency: raw.currency || "USD",
    theme: raw.theme === "dark" ? "dark" : "light",
    monthlyIncome: raw.monthlyIncome,
    remindersEnabled: Boolean(raw.remindersEnabled),
    lastCheckIn: raw.lastCheckIn,
    tombstones: Array.isArray(raw.tombstones) ? raw.tombstones : [],
    settingsUpdatedAt: raw.settingsUpdatedAt || 0,
    syncCode: raw.syncCode,
    syncEnabled: Boolean(raw.syncEnabled),
  };
}

interface StoreContextValue {
  data: AppData;
  ready: boolean;
  storageError?: string;
  member: (id?: string) => Member | undefined;
  addTransaction: (t: Omit<Transaction, "id" | "createdAt">) => void;
  updateTransaction: (id: string, patch: Partial<Transaction>) => void;
  deleteTransaction: (id: string) => void;
  addDebt: (d: Omit<Debt, "id" | "createdAt">) => void;
  updateDebt: (id: string, patch: Partial<Debt>) => void;
  payDebt: (id: string, amount: number, memberId?: string) => void;
  deleteDebt: (id: string) => void;
  applyParsedEntries: (entries: ParsedEntry[], memberId?: string) => void;
  // household / settings
  addMember: (m: Omit<Member, "id">) => string;
  updateMember: (id: string, patch: Partial<Member>) => void;
  removeMember: (id: string) => void;
  setBudget: (category: string, limit: number) => void;
  removeBudget: (category: string) => void;
  addBill: (b: Omit<RecurringBill, "id" | "createdAt">) => void;
  updateBill: (id: string, patch: Partial<RecurringBill>) => void;
  deleteBill: (id: string) => void;
  markBillPaid: (id: string, month?: string) => void;
  addIncome: (x: Omit<RecurringIncome, "id" | "createdAt">) => void;
  updateIncome: (id: string, patch: Partial<RecurringIncome>) => void;
  deleteIncome: (id: string) => void;
  receiveIncome: (id: string, month?: string) => void;
  addBucket: (b: Omit<Bucket, "id" | "createdAt" | "balance"> & { balance?: number }) => void;
  updateBucket: (id: string, patch: Partial<Bucket>) => void;
  deleteBucket: (id: string) => void;
  fundBucket: (id: string, amount: number) => void;
  distributePaycheck: (amount: number) => void;
  addGoal: (g: Omit<Goal, "id" | "createdAt" | "saved"> & { saved?: number }) => void;
  updateGoal: (id: string, patch: Partial<Goal>) => void;
  deleteGoal: (id: string) => void;
  contributeGoal: (id: string, amount: number, memberId?: string) => void;
  addAccount: (a: Omit<Account, "id" | "createdAt">) => void;
  updateAccount: (id: string, patch: Partial<Account>) => void;
  deleteAccount: (id: string) => void;
  setPayCycle: (pc: PayCycle) => void;
  setReminders: (enabled: boolean) => void;
  markCheckIn: () => void;
  setCurrency: (c: string) => void;
  setTheme: (t: ThemeName) => void;
  setHouseholdName: (n: string) => void;
  completeOnboarding: (init: Partial<AppData>) => void;
  importData: (incoming: AppData) => void;
  resetAll: () => void;
  // sync
  setSync: (enabled: boolean, code?: string) => void;
  joinSync: (code: string) => Promise<{ ok: boolean; error?: string }>;
  syncNow: () => Promise<void>;
  syncState: SyncState;
}

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<AppData>(freshData);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState("");

  // Load once on mount.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setData(migrate(JSON.parse(raw)));
    } catch {
      setStorageError("Saved data looked corrupt, so Money Coach opened a fresh local copy.");
    }
    setReady(true);
  }, []);

  // Persist on every change (after initial load).
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      setStorageError("");
    } catch {
      setStorageError("This browser could not save your latest changes. Back up your data and free storage.");
    }
  }, [data, ready]);

  // Reflect theme on <html> so CSS variables switch instantly.
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.dataset.theme = data.theme;
    }
  }, [data.theme]);

  // Auto-log any recurring bills that are marked auto-log and are due (their
  // due day has arrived this month and they haven't been logged yet).
  useEffect(() => {
    if (!ready) return;
    const month = monthKey();
    const now = new Date();
    const today = now.getDate();
    const daysInMonth = new Date(
      now.getFullYear(),
      now.getMonth() + 1,
      0,
    ).getDate();
    setData((d) => {
      const due = (d.recurringBills || []).filter((b) => {
        if (!b.autoLog || b.lastPaidMonth === month) return false;
        return today >= Math.min(b.dayOfMonth, daysInMonth);
      });
      if (due.length === 0) return d;
      const dueIds = new Set(due.map((b) => b.id));
      const nowMs = Date.now();
      return {
        ...d,
        recurringBills: d.recurringBills.map((b) =>
          dueIds.has(b.id) ? { ...b, lastPaidMonth: month, updatedAt: nowMs } : b,
        ),
        transactions: [
          ...due.map((b) => ({
            id: uid(),
            type: "expense" as const,
            amount: Math.abs(b.amount),
            category: b.category,
            description: b.name,
            date: todayISO(),
            memberId: b.memberId,
            createdAt: nowMs,
            updatedAt: nowMs,
          })),
          ...d.transactions,
        ],
      };
    });
  }, [ready]);

  // Auto-log recurring income (e.g. a salary) on/after its day each month, the
  // money-IN twin of the bills auto-log above.
  useEffect(() => {
    if (!ready) return;
    const month = monthKey();
    const now = new Date();
    const today = now.getDate();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    setData((d) => {
      const due = (d.recurringIncome || []).filter((x) => {
        if (!x.autoLog || x.lastPaidMonth === month) return false;
        return today >= Math.min(x.dayOfMonth, daysInMonth);
      });
      if (due.length === 0) return d;
      const dueIds = new Set(due.map((x) => x.id));
      const nowMs = Date.now();
      return {
        ...d,
        recurringIncome: (d.recurringIncome || []).map((x) =>
          dueIds.has(x.id) ? { ...x, lastPaidMonth: month, updatedAt: nowMs } : x,
        ),
        transactions: [
          ...due.map((x) => ({
            id: uid(),
            type: "income" as const,
            amount: Math.abs(x.amount),
            category: "Salary",
            description: x.name,
            date: todayISO(),
            memberId: x.memberId,
            createdAt: nowMs,
            updatedAt: nowMs,
          })),
          ...d.transactions,
        ],
      };
    });
  }, [ready]);

  // Auto-pay recurring debt payments (car loan, student loan, card minimums).
  // On/after the payment day each month, log the minimum, shrink the balance,
  // and record it in the debt's history — once per month per debt.
  useEffect(() => {
    if (!ready) return;
    const month = monthKey();
    const now = new Date();
    const today = now.getDate();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const dayOf = (dbt: Debt): number | null => {
      if (dbt.paymentDay) return Math.min(dbt.paymentDay, daysInMonth);
      if (dbt.dueDate) {
        const day = parseInt(dbt.dueDate.slice(8, 10), 10);
        if (day >= 1 && day <= 31) return Math.min(day, daysInMonth);
      }
      return null;
    };
    setData((d) => {
      const due = d.debts.filter((x) => {
        if (x.direction !== "i_owe" || !x.autoPay || x.lastPaidMonth === month) return false;
        if (!(x.minPayment && x.minPayment > 0) || x.balance <= 0) return false;
        const day = dayOf(x);
        return day != null && today >= day;
      });
      if (due.length === 0) return d;
      const dueIds = new Set(due.map((x) => x.id));
      const nowMs = Date.now();
      const pays = new Map(due.map((x) => [x.id, Math.min(x.minPayment || 0, x.balance)]));
      return {
        ...d,
        debts: d.debts.map((x) =>
          dueIds.has(x.id)
            ? {
                ...x,
                balance: Math.max(0, x.balance - (pays.get(x.id) || 0)),
                lastPaidMonth: month,
                payments: [
                  { id: uid(), amount: pays.get(x.id) || 0, date: todayISO(), createdAt: nowMs, note: "Auto-pay" },
                  ...(x.payments || []),
                ],
                updatedAt: nowMs,
              }
            : x,
        ),
        transactions: [
          ...due.map((x) => ({
            id: uid(),
            type: "expense" as const,
            amount: pays.get(x.id) || 0,
            category: "Debt payment",
            description: `Payment to ${x.party}`,
            date: todayISO(),
            memberId: x.memberId,
            createdAt: nowMs,
            updatedAt: nowMs,
          })),
          ...d.transactions,
        ],
      };
    });
  }, [ready]);

  // Record (or refresh) the current month's net-worth snapshot so we can chart
  // a trend over time. Net worth = accounts + owed-to-you − you-owe.
  useEffect(() => {
    if (!ready) return;
    const month = monthKey();
    setData((d) => {
      const nw =
        (d.accounts || []).reduce((s, a) => s + a.balance, 0) +
        d.debts.filter((x) => x.direction === "owed_to_me").reduce((s, x) => s + x.balance, 0) -
        d.debts.filter((x) => x.direction === "i_owe").reduce((s, x) => s + x.balance, 0);
      const hist = d.netWorthHistory || [];
      const existing = hist.find((p) => p.month === month);
      if (existing && existing.value === nw) return d;
      const next = existing
        ? hist.map((p) => (p.month === month ? { ...p, value: nw } : p))
        : [...hist, { month, value: nw }];
      return { ...d, netWorthHistory: next };
    });
  }, [ready, data.accounts, data.debts]);

  // --- sync engine ---------------------------------------------------------
  const [syncState, setSyncState] = useState<SyncState>("idle");
  const dataRef = useRef(data);
  dataRef.current = data;
  const busyRef = useRef(false);
  const lastPushedRef = useRef("");
  const unconfiguredRef = useRef(false);

  // Fold a remote copy into local state, preserving local-only sync config.
  // Only updates state when something actually changed, to avoid render loops.
  const applyRemote = useCallback((remote: AppData | null) => {
    if (!remote) return;
    // Sanitize untrusted remote data through migrate() (coerces shapes) and
    // guard the merge so a corrupt peer blob can never crash the app.
    let safe: AppData;
    try {
      safe = migrate(remote);
    } catch {
      return;
    }
    setData((local) => {
      try {
        const merged = mergeData(local, safe);
        merged.syncCode = local.syncCode;
        merged.syncEnabled = local.syncEnabled;
        const before = JSON.stringify(sanitizeForSync(local));
        const after = JSON.stringify(sanitizeForSync(merged));
        return before === after ? local : merged;
      } catch {
        return local;
      }
    });
  }, []);

  const syncNow = useCallback(async () => {
    const d = dataRef.current;
    if (!d.syncEnabled || !d.syncCode || busyRef.current) return;
    if (unconfiguredRef.current) return;
    if (typeof navigator !== "undefined" && navigator.onLine === false) return;
    busyRef.current = true;
    setSyncState("syncing");
    try {
      const payload = sanitizeForSync(dataRef.current);
      const res = await fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "push", code: d.syncCode, data: payload }),
      });
      const json = await res.json();
      if (json.configured === false) {
        unconfiguredRef.current = true;
        setSyncState("unconfigured");
        return;
      }
      if (!json.ok) {
        setSyncState("error");
        return;
      }
      applyRemote(json.data);
      lastPushedRef.current = JSON.stringify(sanitizeForSync(dataRef.current));
      setSyncState("ok");
    } catch {
      setSyncState("error");
    } finally {
      busyRef.current = false;
    }
  }, [applyRemote]);

  // Push shortly after local changes (debounced).
  useEffect(() => {
    if (!ready || !data.syncEnabled || !data.syncCode) return;
    const snapshot = JSON.stringify(sanitizeForSync(data));
    if (snapshot === lastPushedRef.current) return;
    const t = setTimeout(() => {
      lastPushedRef.current = snapshot;
      void syncNow();
    }, 1200);
    return () => clearTimeout(t);
  }, [data, ready, syncNow]);

  // Poll for the other phone's changes + on regaining focus.
  useEffect(() => {
    if (!ready || !data.syncEnabled || !data.syncCode) return;
    void syncNow();
    const id = setInterval(() => void syncNow(), 12000);
    const onFocus = () => void syncNow();
    window.addEventListener("focus", onFocus);
    return () => {
      clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, [ready, data.syncEnabled, data.syncCode, syncNow]);

  const member = useCallback(
    (id?: string) => data.members.find((m) => m.id === id),
    [data.members],
  );

  const addTransaction = useCallback(
    (t: Omit<Transaction, "id" | "createdAt">) => {
      const now = Date.now();
      setData((d) => ({
        ...d,
        transactions: [
          { ...t, id: uid(), createdAt: now, updatedAt: now },
          ...d.transactions,
        ],
      }));
    },
    [],
  );

  const updateTransaction = useCallback((id: string, patch: Partial<Transaction>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      transactions: d.transactions.map((t) =>
        t.id === id ? { ...t, ...patch, updatedAt: now } : t,
      ),
    }));
  }, []);

  const deleteTransaction = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      transactions: d.transactions.filter((t) => t.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);

  const addDebt = useCallback((dbt: Omit<Debt, "id" | "createdAt">) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      debts: [
        {
          ...dbt,
          original: dbt.original ?? dbt.balance,
          kind: dbt.kind ?? inferDebtKind(dbt),
          payments: dbt.payments ?? [],
          id: uid(),
          createdAt: now,
          updatedAt: now,
        },
        ...d.debts,
      ],
    }));
  }, []);

  const updateDebt = useCallback((id: string, patch: Partial<Debt>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      debts: d.debts.map((x) => (x.id === id ? { ...x, ...patch, updatedAt: now } : x)),
    }));
  }, []);

  const payDebt = useCallback((id: string, rawAmount: number, memberId?: string) => {
    const amount = Number.isFinite(rawAmount) ? Math.abs(rawAmount) : 0;
    if (amount <= 0) return;
    setData((d) => {
      const target = d.debts.find((x) => x.id === id);
      const now = Date.now();
      const payment = { id: uid(), amount, date: todayISO(), createdAt: now };
      const debts = d.debts.map((x) =>
        x.id === id
          ? {
              ...x,
              balance: Math.max(0, x.balance - amount),
              payments: [payment, ...(x.payments || [])],
              updatedAt: now,
            }
          : x,
      );
      // Log repayments so cash flow and net worth do not silently drift.
      let transactions = d.transactions;
      if (target?.direction === "i_owe") {
        transactions = [
          {
            id: uid(),
            type: "expense",
            amount: Math.abs(amount),
            category: "Debt payment",
            description: `Payment to ${target.party}`,
            date: todayISO(),
            memberId: memberId ?? target.memberId,
            createdAt: now,
            updatedAt: now,
          },
          ...transactions,
        ];
      } else if (target?.direction === "owed_to_me") {
        transactions = [
          {
            id: uid(),
            type: "income",
            amount: Math.abs(amount),
            category: "Debt repayment",
            description: `Repayment from ${target.party}`,
            date: todayISO(),
            memberId: memberId ?? target.memberId,
            createdAt: now,
            updatedAt: now,
          },
          ...transactions,
        ];
      }
      return { ...d, debts, transactions };
    });
  }, []);

  const deleteDebt = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      debts: d.debts.filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);

  // Turn parsed entries from the LLM into stored transactions/debts. We merge
  // debts to the same party + direction instead of creating duplicates.
  const applyParsedEntries = useCallback(
    (entries: ParsedEntry[], memberId?: string) => {
      setData((d) => {
        let txns = d.transactions;
        let debts = d.debts;
        let accounts = d.accounts || [];
        let recurringBills = d.recurringBills || [];
        let budgets = d.budgets || [];
        let goals = d.goals || [];
        const now = Date.now();
        const owner = memberId ?? d.members[0]?.id;
        const ACCT_EMOJI: Record<string, string> = {
          checking: "🏦", savings: "🐷", cash: "💵", investment: "📈", other: "💼",
        };
        const PALETTE = ["#0f766e", "#14b8a6", "#5e7fa6", "#d99a4e", "#7c6ba8", "#2e8b72"];

        for (const e of entries) {
          if (e.kind === "expense" || e.kind === "income") {
            txns = [
              {
                id: uid(),
                type: e.kind,
                amount: Math.abs(e.amount),
                category:
                  e.category || (e.kind === "income" ? "Income" : "Other"),
                description: e.description || e.summary || "",
                date: todayISO(),
                memberId: owner,
                createdAt: now,
                updatedAt: now,
              },
              ...txns,
            ];
          } else if (e.kind === "debt_i_owe" || e.kind === "debt_owed_to_me") {
            const direction =
              e.kind === "debt_i_owe" ? "i_owe" : "owed_to_me";
            const party = (e.party || "Someone").trim();
            const existing = debts.find(
              (x) =>
                x.direction === direction &&
                x.party.toLowerCase() === party.toLowerCase(),
            );
            if (existing) {
              debts = debts.map((x) =>
                x.id === existing.id
                  ? {
                      ...x,
                      balance: x.balance + Math.abs(e.amount),
                      original: (x.original ?? 0) + Math.abs(e.amount),
                      updatedAt: now,
                    }
                  : x,
              );
            } else {
              debts = [
                {
                  id: uid(),
                  direction,
                  kind: inferDebtKind({ party, apr: e.apr }),
                  party,
                  balance: Math.abs(e.amount),
                  original: Math.abs(e.amount),
                  apr: e.apr,
                  payments: [],
                  memberId: owner,
                  createdAt: now,
                  updatedAt: now,
                },
                ...debts,
              ];
            }
          } else if (e.kind === "debt_payment") {
            const party = (e.party || "").trim().toLowerCase();
            const match = debts.find(
              (x) => x.direction === "i_owe" && x.party.toLowerCase() === party,
            );
            if (match) {
              debts = debts.map((x) =>
                x.id === match.id
                  ? {
                      ...x,
                      balance: Math.max(0, x.balance - Math.abs(e.amount)),
                      payments: [
                        { id: uid(), amount: Math.abs(e.amount), date: todayISO(), createdAt: now },
                        ...(x.payments || []),
                      ],
                      updatedAt: now,
                    }
                  : x,
              );
            }
            txns = [
              {
                id: uid(),
                type: "expense",
                amount: Math.abs(e.amount),
                category: "Debt payment",
                description: e.summary || `Payment to ${e.party ?? ""}`,
                date: todayISO(),
                memberId: owner,
                createdAt: now,
                updatedAt: now,
              },
              ...txns,
            ];
          } else if (e.kind === "account") {
            const type = e.accountType || "checking";
            const name = (e.description || `${type[0].toUpperCase()}${type.slice(1)}`).trim();
            const existing = accounts.find((a) => a.name.toLowerCase() === name.toLowerCase());
            if (existing) {
              accounts = accounts.map((a) =>
                a.id === existing.id ? { ...a, balance: Math.abs(e.amount), updatedAt: now } : a,
              );
            } else {
              accounts = [
                {
                  id: uid(), name, type, balance: Math.abs(e.amount),
                  emoji: ACCT_EMOJI[type] || "💼", color: PALETTE[accounts.length % PALETTE.length],
                  memberId: owner, createdAt: now, updatedAt: now,
                },
                ...accounts,
              ];
            }
          } else if (e.kind === "bill") {
            const name = (e.description || e.category || "Bill").trim();
            const existing = recurringBills.find((b) => b.name.toLowerCase() === name.toLowerCase());
            const patch = {
              name, amount: Math.abs(e.amount), category: e.category || "Other",
              dayOfMonth: Math.min(31, Math.max(1, Math.round(e.dayOfMonth || 1))),
            };
            if (existing) {
              recurringBills = recurringBills.map((b) =>
                b.id === existing.id ? { ...b, ...patch, updatedAt: now } : b,
              );
            } else {
              recurringBills = [
                { id: uid(), ...patch, memberId: owner, createdAt: now, updatedAt: now },
                ...recurringBills,
              ];
            }
          } else if (e.kind === "budget") {
            const category = (e.category || e.description || "Other").trim();
            const existing = budgets.find((b) => b.category.toLowerCase() === category.toLowerCase());
            if (existing) {
              budgets = budgets.map((b) =>
                b.category.toLowerCase() === category.toLowerCase()
                  ? { ...b, limit: Math.abs(e.amount), updatedAt: now }
                  : b,
              );
            } else {
              budgets = [...budgets, { category, limit: Math.abs(e.amount), updatedAt: now }];
            }
          } else if (e.kind === "goal") {
            const name = (e.description || "Goal").trim();
            const existing = goals.find((g) => g.name.toLowerCase() === name.toLowerCase());
            if (existing) {
              goals = goals.map((g) =>
                g.id === existing.id
                  ? {
                      ...g,
                      target: Math.abs(e.amount) || g.target,
                      monthlyContribution: e.monthlyContribution ?? g.monthlyContribution,
                      updatedAt: now,
                    }
                  : g,
              );
            } else {
              const target = Number.isFinite(e.amount) && e.amount > 0 ? Math.abs(e.amount) : 0;
              goals = [
                {
                  id: uid(), name, emoji: "🎯", color: PALETTE[goals.length % PALETTE.length],
                  target, saved: 0,
                  monthlyContribution:
                    Number.isFinite(e.monthlyContribution as number) ? e.monthlyContribution : undefined,
                  memberId: owner,
                  createdAt: now, updatedAt: now,
                },
                ...goals,
              ];
            }
          }
        }
        return { ...d, transactions: txns, debts, accounts, recurringBills, budgets, goals };
      });
    },
    [],
  );

  const addMember = useCallback((m: Omit<Member, "id">) => {
    const id = uid();
    setData((d) => ({ ...d, members: [...d.members, { ...m, id, updatedAt: Date.now() }] }));
    return id;
  }, []);

  const updateMember = useCallback((id: string, patch: Partial<Member>) => {
    setData((d) => ({
      ...d,
      members: d.members.map((m) => (m.id === id ? { ...m, ...patch, updatedAt: Date.now() } : m)),
    }));
  }, []);

  const removeMember = useCallback((id: string) => {
    setData((d) => {
      if (d.members.length <= 1) return d; // never leave zero members
      const fallback = d.members.find((m) => m.id !== id)?.id;
      return {
        ...d,
        members: d.members.filter((m) => m.id !== id),
        transactions: d.transactions.map((t) =>
          t.memberId === id ? { ...t, memberId: fallback } : t,
        ),
        debts: d.debts.map((x) =>
          x.memberId === id ? { ...x, memberId: fallback } : x,
        ),
        tombstones: [...(d.tombstones || []), id],
      };
    });
  }, []);

  const setBudget = useCallback((category: string, limit: number) => {
    setData((d) => {
      const now = Date.now();
      const exists = d.budgets.some((b) => b.category === category);
      const budgets = exists
        ? d.budgets.map((b) => (b.category === category ? { ...b, limit, updatedAt: now } : b))
        : [...d.budgets, { category, limit, updatedAt: now }];
      return {
        ...d,
        budgets,
        tombstones: (d.tombstones || []).filter((x) => x !== "budget:" + category),
      };
    });
  }, []);

  const removeBudget = useCallback((category: string) => {
    setData((d) => ({
      ...d,
      budgets: d.budgets.filter((b) => b.category !== category),
      tombstones: [...(d.tombstones || []), "budget:" + category],
    }));
  }, []);

  const addBill = useCallback((b: Omit<RecurringBill, "id" | "createdAt">) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      recurringBills: [
        { ...b, id: uid(), createdAt: now, updatedAt: now },
        ...(d.recurringBills || []),
      ],
    }));
  }, []);

  const updateBill = useCallback((id: string, patch: Partial<RecurringBill>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      recurringBills: (d.recurringBills || []).map((x) =>
        x.id === id ? { ...x, ...patch, updatedAt: now } : x,
      ),
    }));
  }, []);

  const deleteBill = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      recurringBills: (d.recurringBills || []).filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);

  // Mark a bill paid for a given month (default: now): logs the expense and
  // records the month so it stops counting against safe-to-spend.
  const markBillPaid = useCallback((id: string, month: string = monthKey()) => {
    setData((d) => {
      const bill = (d.recurringBills || []).find((x) => x.id === id);
      if (!bill || bill.lastPaidMonth === month) return d;
      const now = Date.now();
      return {
        ...d,
        recurringBills: d.recurringBills.map((x) =>
          x.id === id ? { ...x, lastPaidMonth: month, updatedAt: now } : x,
        ),
        transactions: [
          {
            id: uid(),
            type: "expense" as const,
            amount: Math.abs(bill.amount),
            category: bill.category,
            description: bill.name,
            date: todayISO(),
            memberId: bill.memberId,
            createdAt: now,
            updatedAt: now,
          },
          ...d.transactions,
        ],
      };
    });
  }, []);

  // --- recurring income -----------------------------------------------------
  const addIncome = useCallback((x: Omit<RecurringIncome, "id" | "createdAt">) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      recurringIncome: [{ ...x, id: uid(), createdAt: now, updatedAt: now }, ...(d.recurringIncome || [])],
    }));
  }, []);
  const updateIncome = useCallback((id: string, patch: Partial<RecurringIncome>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      recurringIncome: (d.recurringIncome || []).map((x) => (x.id === id ? { ...x, ...patch, updatedAt: now } : x)),
    }));
  }, []);
  const deleteIncome = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      recurringIncome: (d.recurringIncome || []).filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);
  // Mark an income as received now: log an income transaction + stamp the month.
  const receiveIncome = useCallback((id: string, month: string = monthKey()) => {
    setData((d) => {
      const inc = (d.recurringIncome || []).find((x) => x.id === id);
      if (!inc || inc.lastPaidMonth === month) return d;
      const now = Date.now();
      return {
        ...d,
        recurringIncome: (d.recurringIncome || []).map((x) =>
          x.id === id ? { ...x, lastPaidMonth: month, updatedAt: now } : x,
        ),
        transactions: [
          {
            id: uid(), type: "income" as const, amount: Math.abs(inc.amount), category: "Salary",
            description: inc.name, date: todayISO(), memberId: inc.memberId, createdAt: now, updatedAt: now,
          },
          ...d.transactions,
        ],
      };
    });
  }, []);

  // --- allocation buckets ---------------------------------------------------
  const addBucket = useCallback((b: Omit<Bucket, "id" | "createdAt" | "balance"> & { balance?: number }) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      buckets: [{ ...b, balance: b.balance ?? 0, id: uid(), createdAt: now, updatedAt: now }, ...(d.buckets || [])],
    }));
  }, []);
  const updateBucket = useCallback((id: string, patch: Partial<Bucket>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      buckets: (d.buckets || []).map((x) => (x.id === id ? { ...x, ...patch, updatedAt: now } : x)),
    }));
  }, []);
  const deleteBucket = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      buckets: (d.buckets || []).filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);
  // Move money into (+) or out of (−) a bucket's set-aside balance.
  const fundBucket = useCallback((id: string, amount: number) => {
    const delta = Number.isFinite(amount) ? amount : 0;
    if (delta === 0) return;
    const now = Date.now();
    setData((d) => ({
      ...d,
      buckets: (d.buckets || []).map((x) =>
        x.id === id ? { ...x, balance: Math.max(0, x.balance + delta), updatedAt: now } : x,
      ),
    }));
  }, []);
  // Split a paycheck amount across buckets by their rules (percent of income or
  // a fixed amount), topping up each bucket's balance. Returns nothing; the
  // leftover simply stays as free cash.
  const distributePaycheck = useCallback((amount: number) => {
    const total = Number.isFinite(amount) && amount > 0 ? amount : 0;
    if (total <= 0) return;
    const now = Date.now();
    setData((d) => ({
      ...d,
      buckets: (d.buckets || []).map((x) => {
        if (!x.allocType || !x.allocValue) return x;
        const add = x.allocType === "percent" ? (total * x.allocValue) / 100 : x.allocValue;
        if (add <= 0) return x;
        return { ...x, balance: Math.max(0, x.balance + add), updatedAt: now };
      }),
    }));
  }, []);

  const addGoal = useCallback((g: Omit<Goal, "id" | "createdAt" | "saved"> & { saved?: number }) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      goals: [
        { saved: 0, ...g, id: uid(), createdAt: now, updatedAt: now },
        ...(d.goals || []),
      ],
    }));
  }, []);

  const updateGoal = useCallback((id: string, patch: Partial<Goal>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      goals: (d.goals || []).map((x) => (x.id === id ? { ...x, ...patch, updatedAt: now } : x)),
    }));
  }, []);

  const deleteGoal = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      goals: (d.goals || []).filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);

  // Move money into a goal. Logs it as a "Savings" expense so cash flow reflects
  // that the money is no longer free to spend, and grows the goal balance.
  const contributeGoal = useCallback((id: string, amount: number, memberId?: string) => {
    setData((d) => {
      const goal = (d.goals || []).find((x) => x.id === id);
      if (!goal || amount <= 0) return d;
      const now = Date.now();
      return {
        ...d,
        goals: d.goals.map((x) =>
          x.id === id ? { ...x, saved: x.saved + amount, updatedAt: now } : x,
        ),
        transactions: [
          {
            id: uid(),
            type: "expense" as const,
            amount: Math.abs(amount),
            category: "Savings",
            description: `Saved toward ${goal.name}`,
            date: todayISO(),
            memberId: memberId ?? goal.memberId,
            createdAt: now,
            updatedAt: now,
          },
          ...d.transactions,
        ],
      };
    });
  }, []);

  const addAccount = useCallback((a: Omit<Account, "id" | "createdAt">) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      accounts: [{ ...a, id: uid(), createdAt: now, updatedAt: now }, ...(d.accounts || [])],
    }));
  }, []);

  const updateAccount = useCallback((id: string, patch: Partial<Account>) => {
    const now = Date.now();
    setData((d) => ({
      ...d,
      accounts: (d.accounts || []).map((x) => (x.id === id ? { ...x, ...patch, updatedAt: now } : x)),
    }));
  }, []);

  const deleteAccount = useCallback((id: string) => {
    setData((d) => ({
      ...d,
      accounts: (d.accounts || []).filter((x) => x.id !== id),
      tombstones: [...(d.tombstones || []), id],
    }));
  }, []);

  const setPayCycle = useCallback((pc: PayCycle) => {
    setData((d) => ({ ...d, payCycle: pc, settingsUpdatedAt: Date.now() }));
  }, []);

  const setReminders = useCallback((enabled: boolean) => {
    setData((d) => ({ ...d, remindersEnabled: enabled, settingsUpdatedAt: Date.now() }));
  }, []);

  const markCheckIn = useCallback(() => {
    setData((d) => ({ ...d, lastCheckIn: Date.now() }));
  }, []);

  const setCurrency = useCallback((c: string) => {
    setData((d) => ({ ...d, currency: c, settingsUpdatedAt: Date.now() }));
  }, []);

  const setTheme = useCallback((t: ThemeName) => {
    setData((d) => ({ ...d, theme: t, settingsUpdatedAt: Date.now() }));
  }, []);

  const setHouseholdName = useCallback((n: string) => {
    setData((d) => ({ ...d, householdName: n, settingsUpdatedAt: Date.now() }));
  }, []);

  const completeOnboarding = useCallback((init: Partial<AppData>) => {
    setData((d) => ({
      ...d,
      ...init,
      onboarded: true,
      settingsUpdatedAt: Date.now(),
    }));
  }, []);

  // --- multi-device sync -----------------------------------------------------
  const setSync = useCallback((enabled: boolean, code?: string) => {
    setData((d) => ({
      ...d,
      syncEnabled: enabled,
      syncCode: code !== undefined ? code.trim() : d.syncCode,
    }));
  }, []);

  const joinSync = useCallback(async (code: string) => {
    const clean = code.trim();
    if (clean.length < 12) {
      return { ok: false, error: "Use the full household code from Settings." };
    }
    setSyncState("syncing");
    try {
      const res = await fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "pull", code: clean }),
      });
      const json = await res.json();
      if (json.configured === false) {
        setSyncState("unconfigured");
        return { ok: false, error: "Cloud sync is not configured on this app yet." };
      }
      if (!res.ok || !json.ok) {
        setSyncState("error");
        return { ok: false, error: json.error || "Could not join that household." };
      }
      if (!json.data) {
        setSyncState("error");
        return { ok: false, error: "No household was found for that code." };
      }
      setData((local) => ({
        ...mergeData(local, migrate(json.data)),
        onboarded: true,
        syncEnabled: true,
        syncCode: clean,
      }));
      lastPushedRef.current = JSON.stringify(sanitizeForSync(json.data));
      setSyncState("ok");
      return { ok: true };
    } catch {
      setSyncState("error");
      return { ok: false, error: "Could not reach sync. Try again." };
    }
  }, []);

  const importData = useCallback((incoming: AppData) => {
    setData(() => {
      const valid = parseAppDataInput(incoming);
      if (!valid) return dataRef.current;
      const next = migrate(valid);
      next.syncCode = undefined;
      next.syncEnabled = false;
      return next;
    });
  }, []);

  const resetAll = useCallback(() => setData({ ...freshData(), theme: data.theme }), [data.theme]);

  const value = useMemo<StoreContextValue>(
    () => ({
      data,
      ready,
      storageError,
      member,
      addTransaction,
      updateTransaction,
      deleteTransaction,
      addDebt,
      updateDebt,
      payDebt,
      deleteDebt,
      applyParsedEntries,
      addMember,
      updateMember,
      removeMember,
      setBudget,
      removeBudget,
      addBill,
      updateBill,
      deleteBill,
      markBillPaid,
      addIncome,
      updateIncome,
      deleteIncome,
      receiveIncome,
      addBucket,
      updateBucket,
      deleteBucket,
      fundBucket,
      distributePaycheck,
      addGoal,
      updateGoal,
      deleteGoal,
      contributeGoal,
      addAccount,
      updateAccount,
      deleteAccount,
      setPayCycle,
      setReminders,
      markCheckIn,
      setCurrency,
      setTheme,
      setHouseholdName,
      completeOnboarding,
      importData,
      resetAll,
      setSync,
      joinSync,
      syncNow,
      syncState,
    }),
    [
      data,
      ready,
      storageError,
      member,
      addTransaction,
      updateTransaction,
      deleteTransaction,
      addDebt,
      updateDebt,
      payDebt,
      deleteDebt,
      applyParsedEntries,
      addMember,
      updateMember,
      removeMember,
      setBudget,
      removeBudget,
      addBill,
      updateBill,
      deleteBill,
      markBillPaid,
      addIncome,
      updateIncome,
      deleteIncome,
      receiveIncome,
      addBucket,
      updateBucket,
      deleteBucket,
      fundBucket,
      distributePaycheck,
      addGoal,
      updateGoal,
      deleteGoal,
      contributeGoal,
      addAccount,
      updateAccount,
      deleteAccount,
      setPayCycle,
      setReminders,
      markCheckIn,
      setCurrency,
      setTheme,
      setHouseholdName,
      completeOnboarding,
      importData,
      resetAll,
      setSync,
      joinSync,
      syncNow,
      syncState,
    ],
  );

  return (
    <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
  );
}

export function useStore(): StoreContextValue {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used within StoreProvider");
  return ctx;
}

// --- Derived selectors ------------------------------------------------------

export interface MonthSummary {
  income: number;
  expenses: number;
  net: number;
  totalIOwe: number;
  totalOwedToMe: number;
  billsDue: number; // unpaid recurring bills still committed this month
  safeToSpend: number;
}

// Recurring bills not yet paid for the current month (optionally per-member).
export function unpaidBills(data: AppData, memberId?: string) {
  const month = monthKey();
  return (data.recurringBills || []).filter(
    (b) =>
      b.lastPaidMonth !== month && (!memberId || b.memberId === memberId),
  );
}

// Summarize the current month. Pass a memberId to scope to one person; omit it
// for the whole household.
export function summarize(data: AppData, memberId?: string): MonthSummary {
  const month = monthKey();
  let income = 0;
  let expenses = 0;
  for (const t of data.transactions) {
    if (memberId && t.memberId !== memberId) continue;
    if (!t.date.startsWith(month)) continue;
    if (t.type === "income") income += t.amount;
    else expenses += t.amount;
  }

  const debts = memberId
    ? data.debts.filter((d) => d.memberId === memberId)
    : data.debts;
  const totalIOwe = debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + d.balance, 0);
  const totalOwedToMe = debts
    .filter((d) => d.direction === "owed_to_me")
    .reduce((s, d) => s + d.balance, 0);

  const baselineIncome =
    income ||
    (memberId
      ? data.members.find((m) => m.id === memberId)?.monthlyIncome || 0
      : data.members.reduce((s, m) => s + (m.monthlyIncome || 0), 0) ||
        data.monthlyIncome ||
        0);

  const minDebtDue = debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + (d.minPayment || 0), 0);
  const debtPaidThisMonth = data.transactions
    .filter(
      (t) =>
        t.type === "expense" &&
        t.category === "Debt payment" &&
        t.date.startsWith(month) &&
        (!memberId || t.memberId === memberId),
    )
    .reduce((s, t) => s + t.amount, 0);
  const unpaidDebtMin = Math.max(0, minDebtDue - debtPaidThisMonth);

  // Bills not yet paid this month are committed money — subtract them so the
  // headline "safe to spend" reflects what's genuinely free.
  const billsDue = unpaidBills(data, memberId).reduce(
    (s, b) => s + b.amount,
    0,
  );

  const safeToSpend = baselineIncome - expenses - unpaidDebtMin - billsDue;

  return {
    income,
    expenses,
    net: income - expenses,
    totalIOwe,
    totalOwedToMe,
    billsDue,
    safeToSpend,
  };
}
