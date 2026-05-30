"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { AppData, Debt, Transaction, ParsedEntry } from "./types";
import { uid, todayISO } from "./format";

const STORAGE_KEY = "money-coach-data-v1";

const EMPTY: AppData = {
  transactions: [],
  debts: [],
  currency: "USD",
};

interface StoreContextValue {
  data: AppData;
  ready: boolean;
  addTransaction: (t: Omit<Transaction, "id" | "createdAt">) => void;
  deleteTransaction: (id: string) => void;
  addDebt: (d: Omit<Debt, "id" | "createdAt">) => void;
  updateDebt: (id: string, patch: Partial<Debt>) => void;
  payDebt: (id: string, amount: number) => void;
  deleteDebt: (id: string) => void;
  applyParsedEntries: (entries: ParsedEntry[]) => void;
  setMonthlyIncome: (n: number) => void;
  resetAll: () => void;
}

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<AppData>(EMPTY);
  const [ready, setReady] = useState(false);

  // Load once on mount.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setData({ ...EMPTY, ...JSON.parse(raw) });
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
    }));
  }, []);

  const addDebt = useCallback((dbt: Omit<Debt, "id" | "createdAt">) => {
    setData((d) => ({
      ...d,
      debts: [{ ...dbt, id: uid(), createdAt: Date.now() }, ...d.debts],
    }));
  }, []);

  const updateDebt = useCallback((id: string, patch: Partial<Debt>) => {
    setData((d) => ({
      ...d,
      debts: d.debts.map((x) => (x.id === id ? { ...x, ...patch } : x)),
    }));
  }, []);

  const payDebt = useCallback((id: string, amount: number) => {
    setData((d) => ({
      ...d,
      debts: d.debts.map((x) =>
        x.id === id ? { ...x, balance: Math.max(0, x.balance - amount) } : x,
      ),
    }));
  }, []);

  const deleteDebt = useCallback((id: string) => {
    setData((d) => ({ ...d, debts: d.debts.filter((x) => x.id !== id) }));
  }, []);

  const setMonthlyIncome = useCallback((n: number) => {
    setData((d) => ({ ...d, monthlyIncome: n }));
  }, []);

  // Turn parsed entries from the LLM into stored transactions/debts. We merge
  // debts to the same party + direction instead of creating duplicates.
  const applyParsedEntries = useCallback((entries: ParsedEntry[]) => {
    setData((d) => {
      let txns = d.transactions;
      let debts = d.debts;
      const now = Date.now();

      for (const e of entries) {
        if (e.kind === "expense" || e.kind === "income") {
          txns = [
            {
              id: uid(),
              type: e.kind,
              amount: Math.abs(e.amount),
              category: e.category || (e.kind === "income" ? "Income" : "Other"),
              description: e.description || e.summary || "",
              date: todayISO(),
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
                ? { ...x, balance: x.balance + Math.abs(e.amount) }
                : x,
            );
          } else {
            debts = [
              {
                id: uid(),
                direction,
                party,
                balance: Math.abs(e.amount),
                apr: e.apr,
                createdAt: now,
              },
              ...debts,
            ];
          }
        } else if (e.kind === "debt_payment") {
          // Reduce the matching "i owe" debt; also log it as an expense.
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
              createdAt: now,
            },
            ...txns,
          ];
        }
      }
      return { ...d, transactions: txns, debts };
    });
  }, []);

  const resetAll = useCallback(() => setData(EMPTY), []);

  const value = useMemo(
    () => ({
      data,
      ready,
      addTransaction,
      deleteTransaction,
      addDebt,
      updateDebt,
      payDebt,
      deleteDebt,
      applyParsedEntries,
      setMonthlyIncome,
      resetAll,
    }),
    [
      data,
      ready,
      addTransaction,
      deleteTransaction,
      addDebt,
      updateDebt,
      payDebt,
      deleteDebt,
      applyParsedEntries,
      setMonthlyIncome,
      resetAll,
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

export function summarize(data: AppData): MonthSummary {
  const month = new Date().toISOString().slice(0, 7); // YYYY-MM
  let income = 0;
  let expenses = 0;
  for (const t of data.transactions) {
    if (!t.date.startsWith(month)) continue;
    if (t.type === "income") income += t.amount;
    else expenses += t.amount;
  }
  const totalIOwe = data.debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + d.balance, 0);
  const totalOwedToMe = data.debts
    .filter((d) => d.direction === "owed_to_me")
    .reduce((s, d) => s + d.balance, 0);

  const baseIncome = income || data.monthlyIncome || 0;
  // "Safe to spend" = this month's income minus what's already gone out minus
  // the minimum debt payments still due this month.
  const minDebtDue = data.debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + (d.minPayment || 0), 0);
  const safeToSpend = baseIncome - expenses - minDebtDue;

  return {
    income,
    expenses,
    net: income - expenses,
    totalIOwe,
    totalOwedToMe,
    safeToSpend,
  };
}
