import { NavLink } from "react-router-dom";

const nav = [
  { to: "/", label: "Dashboard", hint: "Overview" },
  { to: "/upload", label: "Upload", hint: "CSV intake" },
  { to: "/transactions", label: "Transactions", hint: "Review + correct" },
  { to: "/analytics", label: "Analytics", hint: "Charts" },
  { to: "/budget", label: "Budget", hint: "Planner" },
  { to: "/insights", label: "Insights", hint: "AI summaries" },
];

export default function Sidebar() {
  return (
    <aside className="panel sticky top-24 h-fit">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Workspace</p>
      <nav className="mt-4 space-y-2">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                "block rounded-[22px] border px-4 py-3 transition",
                isActive
                  ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-100"
                  : "border-transparent bg-white/[0.03] text-slate-300 hover:border-white/10 hover:bg-white/[0.05]",
              ].join(" ")
            }
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">{item.label}</span>
              <span className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{item.hint}</span>
            </div>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
