"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, CreditCard, Home, Target } from "lucide-react";

const TABS = [
  { href: "/", label: "Today", Icon: Home },
  { href: "/plan", label: "Plan", Icon: Target },
  { href: "/spending", label: "Spending", Icon: BarChart3 },
  { href: "/debt", label: "Debt", Icon: CreditCard },
  { href: "/coach", label: "Coach", Icon: Bot },
];

export default function BottomNav() {
  const path = usePathname();
  return (
    <nav className="dock" aria-label="Primary navigation">
      {TABS.map((t) => {
        const active = t.href === "/" ? path === "/" : path.startsWith(t.href);
        return (
          <Link key={t.href} href={t.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined}>
            <t.Icon aria-hidden="true" strokeWidth={2.1} />
            <span>{t.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
