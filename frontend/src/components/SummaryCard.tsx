export default function SummaryCard({ title, value, sub }: { title: string; value: string; sub?: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-400">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-cyan-300">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
