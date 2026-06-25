import type {
  Account,
  AppData,
  Budget,
  Debt,
  Goal,
  Member,
  NetWorthPoint,
  RecurringBill,
  Transaction,
} from "./types";

// Merge two copies of a household's data into one, so two phones editing
// independently never lose each other's work.
//
// Strategy (good enough for a low-write, 2-person household):
//   - Collections (transactions, debts, members, budgets) are unioned by a
//     stable key. If both sides have the same id, the newer one wins.
//   - Deletions are tracked as `tombstones` (the deleted id / budget category),
//     unioned across both sides and then removed from the result — so a delete
//     on one phone doesn't get "undone" by the other phone re-adding it.
//   - Scalar settings (currency, theme, household name, onboarded) come from
//     whichever side has the larger `settingsUpdatedAt`.
//
// The function is commutative and idempotent: merge(a, b) === merge(b, a), and
// merging the same data twice changes nothing.
export function mergeData(a: AppData, b: AppData): AppData {
  const tombstones = unionStrings(a.tombstones, b.tombstones);
  const dead = new Set(tombstones);

  const transactions = unionById(a.transactions, b.transactions, dead, txnTime);
  const debts = unionById(a.debts, b.debts, dead, recordTime);
  let members = unionById(a.members, b.members, dead, memberTime);
  const budgets = unionByKey(a.budgets, b.budgets, (x) => x.category, dead, budgetTime);
  const recurringBills = unionById(
    a.recurringBills,
    b.recurringBills,
    dead,
    recordTime,
  );
  const goals = unionById(a.goals, b.goals, dead, recordTime);
  const accounts = unionById(a.accounts, b.accounts, dead, recordTime);
  const recurringIncome = unionById(a.recurringIncome, b.recurringIncome, dead, recordTime);
  const buckets = unionById(a.buckets, b.buckets, dead, recordTime);
  const wishlist = unionById(a.wishlist, b.wishlist, dead, wishTime);
  // Net-worth history: one point per month, prefer the most recent writer.
  const nwMap = new Map<string, NetWorthPoint>();
  for (const p of [...(a.netWorthHistory || []), ...(b.netWorthHistory || [])]) {
    const prev = nwMap.get(p.month);
    if (!prev || stableStringify(p) >= stableStringify(prev)) nwMap.set(p.month, p);
  }
  const netWorthHistory = [...nwMap.values()].sort((x, y) =>
    x.month.localeCompare(y.month),
  );

  // Never leave a household with zero members.
  if (members.length === 0) {
    members = a.members.length ? a.members : b.members;
  }

  const aNewer = (a.settingsUpdatedAt || 0) >= (b.settingsUpdatedAt || 0);
  const scalarSrc = aNewer ? a : b;

  return {
    version: Math.max(a.version || 1, b.version || 1),
    onboarded: a.onboarded || b.onboarded,
    householdName: scalarSrc.householdName,
    currency: scalarSrc.currency,
    theme: scalarSrc.theme,
    monthlyIncome: scalarSrc.monthlyIncome,
    payCycle: scalarSrc.payCycle || { type: "monthly" },
    remindersEnabled: scalarSrc.remindersEnabled,
    lastCheckIn: Math.max(a.lastCheckIn || 0, b.lastCheckIn || 0) || undefined,
    settingsUpdatedAt: Math.max(a.settingsUpdatedAt || 0, b.settingsUpdatedAt || 0),
    members,
    transactions,
    debts,
    budgets,
    recurringBills,
    recurringIncome,
    buckets,
    wishlist,
    goals,
    accounts,
    netWorthHistory,
    lastPaycheckDistributed:
      (a.lastPaycheckDistributed || "") >= (b.lastPaycheckDistributed || "")
        ? a.lastPaycheckDistributed
        : b.lastPaycheckDistributed,
    tombstones,
    // Sync config is local-only; callers re-attach it after merging.
    syncCode: a.syncCode ?? b.syncCode,
    syncEnabled: a.syncEnabled ?? b.syncEnabled,
  };
}

function txnTime(t: Transaction): number {
  return t.updatedAt || t.createdAt;
}

function recordTime<T extends { createdAt: number; updatedAt?: number }>(x: T): number {
  return x.updatedAt || x.createdAt;
}

function memberTime(m: Member): number {
  return m.updatedAt || 0;
}

function wishTime(w: { createdAt: number; decidedAt?: number }): number {
  return w.decidedAt || w.createdAt;
}

function budgetTime(b: Budget): number {
  return b.updatedAt || 0;
}

function unionById<T extends { id: string }>(
  a: T[] = [],
  b: T[] = [],
  dead: Set<string>,
  time: (x: T) => number,
): T[] {
  const map = new Map<string, T>();
  for (const x of [...a, ...b]) {
    if (dead.has(x.id)) continue;
    const prev = map.get(x.id);
    if (!prev || isPreferred(x, prev, time)) map.set(x.id, x);
  }
  return [...map.values()].sort((x, y) => {
    const byTime = time(y) - time(x);
    return byTime || x.id.localeCompare(y.id);
  });
}

function unionByKey<T>(
  a: T[] = [],
  b: T[] = [],
  key: (x: T) => string,
  dead: Set<string>,
  time: (x: T) => number,
): T[] {
  const map = new Map<string, T>();
  for (const x of [...a, ...b]) {
    const k = key(x);
    if (dead.has("budget:" + k)) continue;
    const prev = map.get(k);
    if (!prev || isPreferred(x, prev, time)) map.set(k, x);
  }
  return [...map.values()].sort((x, y) => key(x).localeCompare(key(y)));
}

function unionStrings(a: string[] = [], b: string[] = []): string[] {
  return [...new Set([...(a || []), ...(b || [])])].sort();
}

function isPreferred<T>(next: T, prev: T, time: (x: T) => number): boolean {
  const nextTime = time(next);
  const prevTime = time(prev);
  if (nextTime !== prevTime) return nextTime > prevTime;
  return stableStringify(next) >= stableStringify(prev);
}

function stableStringify(value: unknown): string {
  return JSON.stringify(sortKeys(value));
}

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (!value || typeof value !== "object") return value;
  return Object.keys(value as Record<string, unknown>)
    .sort()
    .reduce<Record<string, unknown>>((acc, key) => {
      acc[key] = sortKeys((value as Record<string, unknown>)[key]);
      return acc;
    }, {});
}

// Strip local-only fields before writing to the shared cloud blob.
export function sanitizeForSync(data: AppData): AppData {
  const { syncCode, syncEnabled, ...rest } = data;
  return rest as AppData;
}
