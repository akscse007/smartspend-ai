import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getAnalyticsOverview, getIncomeVsExpense } from "../services/api";
import type { AnalyticsOverview } from "../types/transaction";
import { inr } from "../utils/format";

export default function Analytics() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [incomeExpense, setIncomeExpense] = useState<{ month: string; income: number; expense: number }[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [overviewData, incomeExpenseData] = await Promise.all([getAnalyticsOverview(), getIncomeVsExpense()]);
        setOverview(overviewData);
        setIncomeExpense(incomeExpenseData);
      } catch (error: any) {
        toast.error(error?.response?.data?.detail || "Failed to load analytics.");
      }
    };
    void load();
  }, []);

  const monthlyCategorySpend = useMemo(() => {
    if (!overview) {
      return [];
    }

    const grouped = new Map<string, { month: string; total: number }>();
    overview.monthly_category_spending.forEach((row) => {
      const current = grouped.get(row.month) || { month: row.month, total: 0 };
      current.total += row.amount;
      grouped.set(row.month, current);
    });
    return Array.from(grouped.values());
  }, [overview]);

  if (!overview) {
    return <div className="panel">Loading analytics...</div>;
  }

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Monthly spending</p>
          <h2 className="mt-2 text-xl font-semibold">Expense curve</h2>
          <div className="mt-4 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyCategorySpend}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="month" stroke="#89a3ad" />
                <YAxis stroke="#89a3ad" />
                <Tooltip formatter={(value: number) => inr(value)} />
                <Area type="monotone" dataKey="total" stroke="#68e1c2" fill="rgba(104,225,194,0.22)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Cash flow</p>
          <h2 className="mt-2 text-xl font-semibold">Income vs expense</h2>
          <div className="mt-4 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={incomeExpense}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="month" stroke="#89a3ad" />
                <YAxis stroke="#89a3ad" />
                <Tooltip formatter={(value: number) => inr(value)} />
                <Legend />
                <Bar dataKey="income" fill="#56c8ff" radius={[8, 8, 0, 0]} />
                <Bar dataKey="expense" fill="#ff9d66" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Recurring spend</p>
          <h2 className="mt-2 text-xl font-semibold">Subscriptions detected</h2>
          <div className="mt-5 space-y-3">
            {overview.subscriptions.length === 0 && <p className="text-sm muted">No recurring transactions detected yet.</p>}
            {overview.subscriptions.map((item) => (
              <div key={`${item.merchant}-${item.recurrence}`} className="rounded-[20px] border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{item.merchant}</p>
                    <p className="mt-1 text-sm muted">{item.recurrence}</p>
                  </div>
                  <p className="text-sm font-medium">{inr(item.average_amount)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Duplicate detection</p>
          <h2 className="mt-2 text-xl font-semibold">Potential duplicate groups</h2>
          <div className="mt-5 space-y-3">
            {overview.duplicates.length === 0 && <p className="text-sm muted">No duplicate groups found.</p>}
            {overview.duplicates.map((item) => (
              <div key={`${item.description}-${item.amount}`} className="rounded-[20px] border border-white/10 bg-white/[0.03] p-4">
                <p className="font-medium">{item.description}</p>
                <p className="mt-1 text-sm muted">
                  {inr(item.amount)} • {item.count} entries
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
