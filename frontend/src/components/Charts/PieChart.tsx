import { Cell, Pie, PieChart as RPieChart, ResponsiveContainer, Tooltip } from "recharts";

const colors = ["#06b6d4", "#f59e0b", "#8b5cf6", "#22c55e", "#ef4444", "#14b8a6", "#3b82f6"];

export default function PieChartCard({ data }: { data: { category: string; amount: number }[] }) {
  return (
    <div className="card h-[360px]">
      <h3 className="mb-2 text-sm text-slate-400">Category Distribution</h3>
      <ResponsiveContainer width="100%" height="90%">
        <RPieChart>
          <Pie data={data} dataKey="amount" nameKey="category" outerRadius={110} label>
            {data.map((entry, idx) => (
              <Cell key={entry.category} fill={colors[idx % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
        </RPieChart>
      </ResponsiveContainer>
    </div>
  );
}
