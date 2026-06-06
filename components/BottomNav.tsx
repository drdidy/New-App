"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, CreditCard, Home, Target } from "lucide-react";

const TABS = [
  { href: "/", label: "Today", Icon: Home },
  { href: "/plan", label: "Plan", Icon: Target },
  { href: "/insights", label: "Spending", Icon: BarChart3 },
  { href: "/debts", label: "Debt", Icon: CreditCard },
  { href: "/advisor", label: "Coach", Icon: Bot },
];

export default function BottomNav() {
  const path = usePathname();
  return (
    <nav className="nav" aria-label="Primary navigation">
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
    </nav>
  );
}
