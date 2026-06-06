"use client";

import type { Member } from "@/lib/types";
import { initials } from "@/lib/format";

// A colored avatar chip for a household member. Falls back to initials.
export default function Avatar({
  member,
  size = 30,
}: {
  member?: Member;
  size?: number;
}) {
  const color = member?.color || "#8dbbff";
  return (
    <span
      className="avatar"
      title={member?.name}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.5,
        background: `linear-gradient(180deg, ${color}33, ${color}14)`,
        border: `1.5px solid ${color}66`,
        boxShadow: `0 0 12px ${color}33`,
      }}
    >
      {member?.emoji || (member ? initials(member.name) : "?")}
    </span>
  );
}
