import { CartesianGrid, Legend, Line, LineChart as RLineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function TrendLineChart({ data }: { data: { month: string; income: number; expense: number }[] }) {
  return (
    <div className="card h-[360px]">
      <h3 className="mb-2 text-sm text-slate-400">Monthly Trend</h3>
      <ResponsiveContainer width="100%" height="90%">
        <RLineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip />
          <Legend />
          <Line dataKey="expense" stroke="#06b6d4" strokeWidth={2} />
          <Line dataKey="income" stroke="#22c55e" strokeWidth={2} />
        </RLineChart>
      </ResponsiveContainer>
    </div>
  );
}
