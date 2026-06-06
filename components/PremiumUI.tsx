"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="vision-page-head">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </header>
  );
}

export function ActionButton({
  href,
  onClick,
  children,
  variant = "primary",
}: {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
}) {
  const className = `premium-action ${variant === "secondary" ? "secondary" : ""}`;
  const content = (
    <>
      <span>{children}</span>
      <ArrowRight size={15} aria-hidden="true" />
    </>
  );

  if (href) {
    return (
      <Link href={href} className={className}>
        {content}
      </Link>
    );
  }

  return (
    <button className={className} onClick={onClick} type="button">
      {content}
    </button>
  );
}

export function EmptyState({
  Icon,
  title,
  body,
  action,
  href,
  secondary,
}: {
  Icon: LucideIcon;
  title: string;
  body: string;
  action?: string;
  href?: string;
  secondary?: string;
}) {
  return (
    <div className="premium-empty-state">
      <span className="premium-empty-icon">
        <Icon size={22} aria-hidden="true" />
      </span>
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
        {action && <ActionButton href={href} variant="secondary">{action}</ActionButton>}
        {secondary && <small>{secondary}</small>}
      </div>
    </div>
  );
}

export function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <article className={`vision-card ${className}`}>{children}</article>;
}

export function MetricCard({
  label,
  value,
  helper,
  className = "",
}: {
  label: string;
  value: React.ReactNode;
  helper?: React.ReactNode;
  className?: string;
}) {
  return (
    <GlassCard className={`metric-card ${className}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper && <small>{helper}</small>}
    </GlassCard>
  );
}

export function StatPill({ children }: { children: React.ReactNode }) {
  return <span className="stat-pill">{children}</span>;
}

export function ChartCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <GlassCard className={`chart-card ${className}`}>{children}</GlassCard>;
}

export { default as ProgressRing } from "@/components/Ring";
export function CoachChatPanel({ children }: { children: React.ReactNode }) {
  return <GlassCard className="chat-panel span-7">{children}</GlassCard>;
}
