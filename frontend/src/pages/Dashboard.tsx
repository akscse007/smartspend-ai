import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import {
  categorizeExpense,
  getAlerts,
  getAnalyticsOverview,
  getBudgetInsights,
  getCashflowCalendar,
  getMerchantIntelligence,
  getMonthlyTrend,
  listNotifications,
  markNotificationRead,
} from "../services/api";
import type {
  AlertItem,
  AnalyticsOverview,
  AppNotification,
  BudgetInsights,
  CashflowCalendar,
  CategorizeResult,
  MerchantIntelligence,
} from "../types/transaction";
import { inr, percent } from "../utils/format";

const COLORS = ["#68e1c2", "#56c8ff", "#f1c75b", "#ff7d6b", "#ae8cff", "#8de1a1"];

const formatShortDate = (value: string) =>
  new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [budgetInsights, setBudgetInsights] = useState<BudgetInsights | null>(null);
  const [cashflow, setCashflow] = useState<CashflowCalendar | null>(null);
  const [merchantIntel, setMerchantIntel] = useState<MerchantIntelligence | null>(null);
  const [trend, setTrend] = useState<{ month: string; income: number; expense: number }[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [checkingText, setCheckingText] = useState("Uber ride to office");
  const [prediction, setPrediction] = useState<CategorizeResult | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [analyticsData, budgetData, trendData, alertData, notificationData, cashflowData, merchantData] = await Promise.all([
        getAnalyticsOverview(),
        getBudgetInsights(),
        getMonthlyTrend(),
        getAlerts(),
        listNotifications({ limit: 6 }),
        getCashflowCalendar(),
        getMerchantIntelligence(),
      ]);
      setAnalytics(analyticsData);
      setBudgetInsights(budgetData);
      setTrend(trendData);
      setAlerts(alertData.alerts || []);
      setNotifications(notificationData);
      setCashflow(cashflowData);
      setMerchantIntel(merchantData);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleCategorize = async () => {
    try {
      const result = await categorizeExpense(checkingText);
      setPrediction(result);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Prediction failed.");
    }
  };

  const handleMarkRead = async (id: number) => {
    await markNotificationRead(id, true);
    await load();
  };

  if (loading || !analytics || !budgetInsights || !cashflow || !merchantIntel) {
    return <div className="panel">Loading dashboard...</div>;
  }

  const overview = budgetInsights.overview;

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="Operate your budget like a control room"
        description="Watch category drift, review upcoming cashflow, pressure-test monthly decisions, and keep merchant risk visible in one place."
        badge={overview.month}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total spending" value={inr(overview.total_spending)} hint={`Current month ${overview.month}`} icon="wallet" tone="primary" />
        <MetricCard label="Monthly budget" value={inr(overview.monthly_budget)} hint="Configured category budgets" icon="budget" />
        <MetricCard label="Top category" value={overview.top_category} hint="Largest expense bucket this month" icon="analytics" />
        <MetricCard
          label="Remaining budget"
          value={inr(overview.remaining_budget)}
          hint="Budget runway for the month"
          icon="target"
          tone={overview.remaining_budget < 0 ? "warning" : "success"}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="panel panel-strong">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Spending mix</p>
              <h2 className="text-xl font-semibold">Category distribution</h2>
            </div>
            <span className="pill">{analytics.overview.month}</span>
          </div>
          <div className="chart-shell h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={analytics.category_distribution} dataKey="amount" nameKey="category" innerRadius={70} outerRadius={110}>
                  {analytics.category_distribution.map((entry, index) => (
                    <Cell key={entry.category} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => inr(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">AI check</p>
            <h2 className="text-xl font-semibold">Categorize before import</h2>
            <p className="mt-2 text-sm muted">Validate how the model reads merchant text before it hits the transaction queue.</p>
          </div>
          <input className="field" placeholder="Type a sample transaction" value={checkingText} onChange={(event) => setCheckingText(event.target.value)} />
          <button className="button-primary w-full" onClick={handleCategorize}>
            Run categorizer
          </button>
          {prediction && (
            <div className="surface-subtle">
              <div className="flex items-center justify-between gap-3">
                <p className="text-base font-semibold text-white">{prediction.predicted_category}</p>
                <span className="badge-soft">{percent(prediction.confidence)}</span>
              </div>
              <p className="mt-2 text-sm muted">{prediction.merchant}</p>
              <p className="mt-3 text-xs uppercase tracking-[0.2em] text-slate-500">{prediction.model_source}</p>
            </div>
          )}
          <div className="surface-subtle">
            <p className="text-sm font-medium">Budget forecast</p>
            <p className="mt-2 text-2xl font-semibold">{inr(analytics.forecast.predicted_amount)}</p>
            <p className="mt-1 text-sm muted">Projected for {analytics.forecast.month}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="panel">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Upcoming cashflow</p>
            <h2 className="text-xl font-semibold">Next {cashflow.window_days} days</h2>
            <p className="mt-2 text-sm muted">Projected from your latest recurring transactions and active savings goals.</p>
          </div>
          <div className="mini-stat-grid">
            <div className="mini-stat">
              <p className="mini-stat-label">Income</p>
              <p className="mini-stat-value">{inr(cashflow.expected_income)}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Outflow</p>
              <p className="mini-stat-value">{inr(cashflow.expected_expense)}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Net</p>
              <p className="mini-stat-value">{inr(cashflow.expected_net)}</p>
            </div>
          </div>
          <div className="timeline-list mt-5">
            {cashflow.events.length === 0 && <p className="text-sm muted">No recurring events detected yet.</p>}
            {cashflow.events.map((event, index) => (
              <div key={`${event.title}-${event.date}-${index}`} className="timeline-item">
                <div className="timeline-date">{formatShortDate(event.date)}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{event.title}</p>
                      <p className="mt-1 text-sm muted">{event.note || "Projected cashflow event"}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-semibold ${event.type === "income" ? "text-emerald-300" : "text-slate-100"}`}>
                        {event.type === "income" ? "+" : "-"}
                        {inr(event.amount)}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{event.cadence || event.type}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Income vs expense</p>
            <h2 className="text-xl font-semibold">Monthly trend</h2>
          </div>
          <div className="chart-shell h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trend}>
                <XAxis dataKey="month" stroke="#89a3ad" />
                <YAxis stroke="#89a3ad" />
                <Tooltip formatter={(value: number) => inr(value)} />
                <Legend />
                <Bar dataKey="income" fill="#56c8ff" radius={[8, 8, 0, 0]} />
                <Bar dataKey="expense" fill="#68e1c2" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Merchant intelligence</p>
              <h2 className="text-xl font-semibold">Who is driving spend</h2>
            </div>
            <span className="pill">{merchantIntel.month}</span>
          </div>
          <div className="mini-stat-grid">
            <div className="mini-stat">
              <p className="mini-stat-label">Tracked spend</p>
              <p className="mini-stat-value">{inr(merchantIntel.total_spend)}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Top 3 share</p>
              <p className="mini-stat-value">{merchantIntel.concentration_share.toFixed(0)}%</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Repeat share</p>
              <p className="mini-stat-value">{merchantIntel.repeat_merchant_share.toFixed(0)}%</p>
            </div>
          </div>
          <div className="mt-5 space-y-3">
            {merchantIntel.top_merchants.map((merchant) => (
              <div key={merchant.merchant} className="merchant-row">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{merchant.merchant}</p>
                    <p className="mt-1 text-sm muted">
                      {merchant.transaction_count} transactions | avg ticket {inr(merchant.average_ticket)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-base font-semibold text-white">{inr(merchant.total_spend)}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{merchant.share_of_spend.toFixed(1)}% of spend</p>
                  </div>
                </div>
                <div className="merchant-bar">
                  <div className="merchant-bar-fill" style={{ width: `${Math.min(merchant.share_of_spend, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 space-y-2">
            {merchantIntel.watchlist.map((item) => (
              <div key={item} className="surface-subtle text-sm">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Signals and queue</p>
            <h2 className="text-xl font-semibold">Alerts + notifications</h2>
          </div>
          {alerts.length > 0 && (
            <div className="mb-4 rounded-[22px] border border-amber-300/20 bg-amber-300/10 p-4">
              <p className="text-sm font-medium text-amber-100">Active alerts</p>
              <div className="mt-3 space-y-2 text-sm text-amber-50/90">
                {alerts.map((alert) => (
                  <div key={alert.message}>{alert.message}</div>
                ))}
              </div>
            </div>
          )}
          <div className="space-y-3">
            {notifications.length === 0 && <p className="text-sm muted">No notifications yet.</p>}
            {notifications.map((notification) => (
              <div key={notification.id} className="surface-subtle">
                <p className="text-sm text-slate-100">{notification.message}</p>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                  <span>{new Date(notification.created_at).toLocaleString()}</span>
                  {!notification.is_read && (
                    <button className="button-secondary px-3 py-2 text-xs" onClick={() => handleMarkRead(notification.id)}>
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
