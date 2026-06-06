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
  Budget,
  Debt,
  Goal,
  Member,
  PayCycle,
  RecurringBill,
  ThemeName,
  Transaction,
  ParsedEntry,
} from "./types";
import { uid, todayISO, monthKey } from "./format";
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

  const transactions: Transaction[] = (raw.transactions || []).map((t: Transaction) =>
    touch(attribute(t), t.updatedAt || t.createdAt || now),
  );
  const debts: Debt[] = (raw.debts || []).map((d: Debt) => ({
    ...touch(attribute(d), d.updatedAt || d.createdAt || now),
    original: d.original ?? d.balance,
  }));
  const recurringBills: RecurringBill[] = (Array.isArray(raw.recurringBills) ? raw.recurringBills : []).map(
    (b: RecurringBill) => touch(attribute(b), b.updatedAt || b.createdAt || now),
  );
  const goals: Goal[] = (Array.isArray(raw.goals) ? raw.goals : []).map((g: Goal) =>
    touch(attribute(g), g.updatedAt || g.createdAt || now),
  );
  const accounts: Account[] = (Array.isArray(raw.accounts) ? raw.accounts : []).map((a: Account) =>
    touch(attribute(a), a.updatedAt || a.createdAt || now),
  );

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
      ? raw.budgets.map((b: Budget) => ({ ...b, updatedAt: b.updatedAt || raw.settingsUpdatedAt || now }))
      : [],
    recurringBills,
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
    setData((local) => {
      const merged = mergeData(local, remote);
      merged.syncCode = local.syncCode;
      merged.syncEnabled = local.syncEnabled;
      const before = JSON.stringify(sanitizeForSync(local));
      const after = JSON.stringify(sanitizeForSync(merged));
      return before === after ? local : merged;
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
        { ...dbt, original: dbt.original ?? dbt.balance, id: uid(), createdAt: now, updatedAt: now },
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

  const payDebt = useCallback((id: string, amount: number, memberId?: string) => {
    setData((d) => {
      const target = d.debts.find((x) => x.id === id);
      const now = Date.now();
      const debts = d.debts.map((x) =>
        x.id === id ? { ...x, balance: Math.max(0, x.balance - amount), updatedAt: now } : x,
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
        const now = Date.now();
        const owner = memberId ?? d.members[0]?.id;

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
                  party,
                  balance: Math.abs(e.amount),
                  original: Math.abs(e.amount),
                  apr: e.apr,
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
                  ? { ...x, balance: Math.max(0, x.balance - Math.abs(e.amount)), updatedAt: now }
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
          }
        }
        return { ...d, transactions: txns, debts };
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
