import type { ReactNode } from "react";

type Accent = "cyan" | "violet" | "green" | "orange";

export function StatCard({
  label,
  value,
  note,
  icon,
  accent,
}: {
  label: string;
  value: string;
  note: string;
  icon: ReactNode;
  accent: Accent;
}) {
  return (
    <article className={`stat-card ${accent}`}>
      <div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}
