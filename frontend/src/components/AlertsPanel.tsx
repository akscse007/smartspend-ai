import { AlertItem } from "../types/transaction";

export default function AlertsPanel({ alerts }: { alerts: AlertItem[] }) {
  if (!alerts.length) {
    return <div className="card text-sm text-emerald-300">No overspending alerts.</div>;
  }

  return (
    <div className="card space-y-2">
      {alerts.map((alert, idx) => (
        <div
          key={`${alert.message}-${idx}`}
          className={`rounded-lg border p-3 text-sm ${
            alert.severity === "high"
              ? "border-rose-500/40 bg-rose-900/20 text-rose-200"
              : "border-amber-500/40 bg-amber-900/20 text-amber-200"
          }`}
        >
          {alert.message}
        </div>
      ))}
    </div>
  );
}
