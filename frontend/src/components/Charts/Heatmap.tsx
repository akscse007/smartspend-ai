export default function Heatmap({ data }: { data: { date: string; amount: number }[] }) {
  const max = Math.max(...data.map((d) => d.amount), 1);

  return (
    <div className="card">
      <h3 className="mb-2 text-sm text-slate-400">Daily Spending Heatmap</h3>
      <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
        {data.slice(-30).map((d) => {
          const intensity = Math.min(d.amount / max, 1);
          const alpha = 0.2 + intensity * 0.8;
          return (
            <div key={d.date} className="rounded-md p-2 text-xs" style={{ backgroundColor: `rgba(6,182,212,${alpha})` }}>
              <div>{d.date.slice(5)}</div>
              <div>INR {Math.round(d.amount)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
