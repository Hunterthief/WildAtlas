import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon?: ReactNode;
  label: string;
  value?: ReactNode;
  className?: string;
}

/** Compact labelled stat card used in the detail-page sidebars. */
export function StatCard({ icon, label, value, className }: StatCardProps) {
  return (
    <div className={cn("rounded-lg border border-border bg-card p-4", className)}>
      <div className="mb-2 flex items-center gap-2 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
        {icon ? <span className="shrink-0 text-muted-foreground">{icon}</span> : null}
        {label}
      </div>
      <div className="text-sm font-semibold text-foreground">{value ?? "—"}</div>
    </div>
  );
}
