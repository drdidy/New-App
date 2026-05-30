"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/", label: "Home", ico: "🏠" },
  { href: "/insights", label: "Insights", ico: "📊" },
  { href: "/debts", label: "Debts", ico: "🤝" },
  { href: "/advisor", label: "Coach", ico: "💬" },
  { href: "/settings", label: "You", ico: "⚙️" },
];

export default function BottomNav() {
  const path = usePathname();
  return (
    <nav className="nav">
      <div className="nav-inner">
        {TABS.map((t) => {
          const active = t.href === "/" ? path === "/" : path.startsWith(t.href);
          return (
            <Link key={t.href} href={t.href} className={active ? "active" : ""}>
              <span className="ico">{t.ico}</span>
              <span>{t.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
