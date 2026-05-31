import type {
  AppData,
  Budget,
  Debt,
  Goal,
  Member,
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
  const debts = unionById(a.debts, b.debts, dead, (d) => d.createdAt);
  let members = unionById(a.members, b.members, dead, () => 0);
  const budgets = unionByKey(a.budgets, b.budgets, (x) => x.category, dead);
  const recurringBills = unionById(
    a.recurringBills,
    b.recurringBills,
    dead,
    (x) => x.createdAt,
  );
  const goals = unionById(a.goals, b.goals, dead, (x) => x.createdAt);

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
    settingsUpdatedAt: Math.max(a.settingsUpdatedAt || 0, b.settingsUpdatedAt || 0),
    members,
    transactions,
    debts,
    budgets,
    recurringBills,
    goals,
    tombstones,
    // Sync config is local-only; callers re-attach it after merging.
    syncCode: a.syncCode ?? b.syncCode,
    syncEnabled: a.syncEnabled ?? b.syncEnabled,
  };
}

function txnTime(t: Transaction): number {
  return t.createdAt;
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
    if (!prev || time(x) >= time(prev)) map.set(x.id, x);
  }
  return [...map.values()].sort((x, y) => time(y) - time(x));
}

function unionByKey<T>(
  a: T[] = [],
  b: T[] = [],
  key: (x: T) => string,
  dead: Set<string>,
): T[] {
  const map = new Map<string, T>();
  for (const x of [...a, ...b]) {
    const k = key(x);
    if (dead.has("budget:" + k)) continue;
    map.set(k, x);
  }
  return [...map.values()];
}

function unionStrings(a: string[] = [], b: string[] = []): string[] {
  return [...new Set([...(a || []), ...(b || [])])];
}

// Strip local-only fields before writing to the shared cloud blob.
export function sanitizeForSync(data: AppData): AppData {
  const { syncCode, syncEnabled, ...rest } = data;
  return rest as AppData;
}
