"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowRight,
  BarChart3,
  Bot,
  CreditCard,
  Home,
  Settings,
  Target,
} from "lucide-react";
import { useStore } from "@/lib/store";

const TABS = [
  { href: "/", label: "Today", Icon: Home },
  { href: "/plan", label: "Plan", Icon: Target },
  { href: "/spending", label: "Spending", Icon: BarChart3 },
  { href: "/debt", label: "Debt", Icon: CreditCard },
  { href: "/coach", label: "Coach", Icon: Bot },
];

export default function BottomNav() {
  const path = usePathname();
  const { data } = useStore();
  const person = data.members[0];
  const displayName = person?.name || "David";
  const initials = displayName
    ?.split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() || "MC";
  const profileLabel =
    data.members.length > 1
      ? `${data.members.length} member household`
      : data.syncEnabled
        ? "Synced profile"
        : "Private local profile";

  return (
    <nav className="nav" aria-label="Primary navigation">
      <div className="nav-desktop-brand">
        <Link href="/" className="nav-brand-lockup">
          <span className="brand-mark">MC</span>
          <strong>Money Coach</strong>
        </Link>
      </div>
      <div className="nav-inner">
        {TABS.map((t) => {
          const active = t.href === "/" ? path === "/" : path.startsWith(t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              className={active ? "active" : ""}
              aria-current={active ? "page" : undefined}
            >
              <t.Icon className="ico" aria-hidden="true" strokeWidth={2.2} />
              <span>{t.label}</span>
            </Link>
          );
        })}
      </div>
      <div className="nav-desktop-coach">
        <strong>Private money intelligence.</strong>
        <span>Ask Coach for the next calm, useful move.</span>
        <Link href="/coach">
          Chat with Coach
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>
      <div className="nav-profile">
        <div className="nav-avatar">{initials}</div>
        <div>
          <strong>{displayName}</strong>
          <span>{profileLabel}</span>
        </div>
        <Link href="/settings" aria-label="Settings">
          <Settings size={16} aria-hidden="true" />
        </Link>
      </div>
    </nav>
  );
}
