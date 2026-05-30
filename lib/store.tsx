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
  AppData,
  Budget,
  Debt,
  Member,
  ThemeName,
  Transaction,
  ParsedEntry,
} from "./types";
import { uid, todayISO, monthKey } from "./format";
import { mergeData, sanitizeForSync } from "./merge";

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
    currency: "USD",
    theme: "dark",
    tombstones: [],
    settingsUpdatedAt: 0,
    syncEnabled: false,
  };
}

// Bring any older/partial saved blob up to the current shape so upgrades never
// wipe a user's data.
function migrate(raw: any): AppData {
  const base = freshData();
  if (!raw || typeof raw !== "object") return base;

  const members: Member[] = Array.isArray(raw.members) ? raw.members : [];
  // v1 had no members — create a default one and attribute existing items to it.
  let defaultMemberId: string | undefined;
  if (members.length === 0) {
    defaultMemberId = uid();
    members.push({
      id: defaultMemberId,
      name: "You",
      emoji: "🦊",
      color: "#5fe0a6",
      monthlyIncome: raw.monthlyIncome,
    });
  }

  const attribute = <T extends { memberId?: string }>(x: T): T =>
    x.memberId ? x : { ...x, memberId: members[0]?.id };

  const transactions: Transaction[] = (raw.transactions || []).map(attribute);
  const debts: Debt[] = (raw.debts || []).map((d: Debt) => ({
    ...attribute(d),
    original: d.original ?? d.balance,
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
    budgets: Array.isArray(raw.budgets) ? raw.budgets : [],
    currency: raw.currency || "USD",
    theme: raw.theme === "light" ? "light" : "dark",
    monthlyIncome: raw.monthlyIncome,
    tombstones: Array.isArray(raw.tombstones) ? raw.tombstones : [],
    settingsUpdatedAt: raw.settingsUpdatedAt || 0,
    syncCode: raw.syncCode,
    syncEnabled: Boolean(raw.syncEnabled),
  };
}

interface StoreContextValue {
  data: AppData;
  ready: boolean;
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
  setCurrency: (c: string) => void;
  setTheme: (t: ThemeName) => void;
  setHouseholdName: (n: string) => void;
  completeOnboarding: (init: Partial<AppData>) => void;
  importData: (incoming: AppData) => void;
  resetAll: () => void;
  // sync
  setSync: (enabled: boolean, code?: string) => void;
  syncNow: () => Promise<void>;
  syncState: SyncState;
}

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<AppData>(freshData);
  const [ready, setReady] = useState(false);

  // Load once on mount.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setData(migrate(JSON.parse(raw)));
    } catch {
      /* ignore corrupt storage */
    }
    setReady(true);
  }, []);

  // Persist on every change (after initial load).
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      /* storage full or unavailable */
    }
  }, [data, ready]);

  // Reflect theme on <html> so CSS variables switch instantly.
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.dataset.theme = data.theme;
    }
  }, [data.theme]);

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
      setData((d) => ({
        ...d,
        transactions: [
          { ...t, id: uid(), createdAt: Date.now() },
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
    setData((d) => ({
      ...d,
      debts: [
        { ...dbt, original: dbt.original ?? dbt.balance, id: uid(), createdAt: Date.now() },
        ...d.debts,
      ],
    }));
  }, []);

  const updateDebt = useCallback((id: string, patch: Partial<Debt>) => {
    setData((d) => ({
      ...d,
      debts: d.debts.map((x) => (x.id === id ? { ...x, ...patch } : x)),
    }));
  }, []);

  const payDebt = useCallback((id: string, amount: number, memberId?: string) => {
    setData((d) => {
      const target = d.debts.find((x) => x.id === id);
      const debts = d.debts.map((x) =>
        x.id === id ? { ...x, balance: Math.max(0, x.balance - amount) } : x,
      );
      // Log an "I owe" repayment as an expense so it shows in cash flow.
      let transactions = d.transactions;
      if (target && target.direction === "i_owe") {
        transactions = [
          {
            id: uid(),
            type: "expense",
            amount: Math.abs(amount),
            category: "Debt payment",
            description: `Payment to ${target.party}`,
            date: todayISO(),
            memberId: memberId ?? target.memberId,
            createdAt: Date.now(),
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
                  ? { ...x, balance: Math.max(0, x.balance - Math.abs(e.amount)) }
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
    setData((d) => ({ ...d, members: [...d.members, { ...m, id }] }));
    return id;
  }, []);

  const updateMember = useCallback((id: string, patch: Partial<Member>) => {
    setData((d) => ({
      ...d,
      members: d.members.map((m) => (m.id === id ? { ...m, ...patch } : m)),
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
      const exists = d.budgets.some((b) => b.category === category);
      const budgets = exists
        ? d.budgets.map((b) => (b.category === category ? { ...b, limit } : b))
        : [...d.budgets, { category, limit }];
      return { ...d, budgets };
    });
  }, []);

  const removeBudget = useCallback((category: string) => {
    setData((d) => ({
      ...d,
      budgets: d.budgets.filter((b) => b.category !== category),
      tombstones: [...(d.tombstones || []), "budget:" + category],
    }));
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

  const importData = useCallback((incoming: AppData) => {
    setData(migrate(incoming));
  }, []);

  const resetAll = useCallback(() => setData({ ...freshData(), theme: data.theme }), [data.theme]);

  const value = useMemo<StoreContextValue>(
    () => ({
      data,
      ready,
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
      setCurrency,
      setTheme,
      setHouseholdName,
      completeOnboarding,
      importData,
      resetAll,
      setSync,
      syncNow,
      syncState,
    }),
    [
      data,
      ready,
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
      setCurrency,
      setTheme,
      setHouseholdName,
      completeOnboarding,
      importData,
      resetAll,
      setSync,
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
  safeToSpend: number;
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
  const safeToSpend = baselineIncome - expenses - minDebtDue;

  return {
    income,
    expenses,
    net: income - expenses,
    totalIOwe,
    totalOwedToMe,
    safeToSpend,
  };
}
