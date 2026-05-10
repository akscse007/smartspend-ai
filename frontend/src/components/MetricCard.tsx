import type { ReactNode } from "react";

import AppIcon from "./AppIcon";

type MetricCardProps = {
  label: string;
  value: string;
  hint: string;
  icon: "wallet" | "budget" | "target" | "trending" | "chart" | "analytics" | "sparkles";
  tone?: "default" | "primary" | "success" | "warning";
  detail?: ReactNode;
};

const toneClass: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "metric-card-icon",
  primary: "metric-card-icon metric-card-icon-primary",
  success: "metric-card-icon metric-card-icon-success",
  warning: "metric-card-icon metric-card-icon-warning",
};

export default function MetricCard({ label, value, hint, icon, tone = "default", detail }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="section-kicker">{label}</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight text-white">{value}</p>
          <p className="mt-2 text-sm text-slate-400">{hint}</p>
        </div>
        <div className={toneClass[tone]}>
          <AppIcon name={icon} className="h-5 w-5" />
        </div>
      </div>
      {detail && <div className="mt-5 text-sm text-slate-300">{detail}</div>}
    </div>
  );
}
