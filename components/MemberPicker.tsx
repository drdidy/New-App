"use client";

import type { Member } from "@/lib/types";

// A compact row of member chips for choosing "who". Optionally includes an
// "Everyone"/"Both" option (value = undefined) for household-wide views.
export default function MemberPicker({
  members,
  value,
  onChange,
  allLabel,
  size = "md",
}: {
  members: Member[];
  value: string | undefined;
  onChange: (id: string | undefined) => void;
  allLabel?: string; // if set, shows an "all" chip mapped to undefined
  size?: "sm" | "md";
}) {
  return (
    <div className={"seg " + (size === "sm" ? "seg-sm" : "")} role="tablist">
      {allLabel && (
        <button
          className={"seg-btn" + (value === undefined ? " on" : "")}
          onClick={() => onChange(undefined)}
          type="button"
        >
          {allLabel}
        </button>
      )}
      {members.map((m) => (
        <button
          key={m.id}
          className={"seg-btn" + (value === m.id ? " on" : "")}
          onClick={() => onChange(m.id)}
          type="button"
          style={
            value === m.id
              ? { borderColor: m.color + "aa", boxShadow: `0 0 0 3px ${m.color}22` }
              : undefined
          }
        >
          <span style={{ marginRight: 5 }}>{m.emoji}</span>
          {m.name}
        </button>
      ))}
    </div>
  );
}
