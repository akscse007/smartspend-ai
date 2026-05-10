import { Bar, BarChart as RBarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function IncomeExpenseBar({ data }: { data: { month: string; income: number; expense: number }[] }) {
  return (
    <div className="card h-[360px]">
      <h3 className="mb-2 text-sm text-slate-400">Income vs Expense</h3>
      <ResponsiveContainer width="100%" height="90%">
        <RBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip />
          <Legend />
          <Bar dataKey="income" fill="#22c55e" radius={[6, 6, 0, 0]} />
          <Bar dataKey="expense" fill="#06b6d4" radius={[6, 6, 0, 0]} />
        </RBarChart>
      </ResponsiveContainer>
    </div>
  );
}
