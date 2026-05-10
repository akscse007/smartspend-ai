import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader";
import { getAnalyticsOverview, getBudgetInsights, getFeedbackInsights, getMerchantIntelligence } from "../services/api";
import type { AnalyticsOverview, BudgetInsights, FeedbackInsights, MerchantIntelligence } from "../types/transaction";
import { inr } from "../utils/format";

export default function Insights() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [budgetInsights, setBudgetInsights] = useState<BudgetInsights | null>(null);
  const [feedbackInsights, setFeedbackInsights] = useState<FeedbackInsights | null>(null);
  const [merchantIntel, setMerchantIntel] = useState<MerchantIntelligence | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [analyticsData, budgetData, feedbackData, merchantData] = await Promise.all([
          getAnalyticsOverview(),
          getBudgetInsights(),
          getFeedbackInsights(),
          getMerchantIntelligence(),
        ]);
        setAnalytics(analyticsData);
        setBudgetInsights(budgetData);
        setFeedbackInsights(feedbackData);
        setMerchantIntel(merchantData);
      } catch (error: any) {
        toast.error(error?.response?.data?.detail || "Failed to load insights.");
      }
    };
    void load();
  }, []);

  if (!analytics || !budgetInsights || !feedbackInsights || !merchantIntel) {
    return <div className="panel">Loading insights...</div>;
  }

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Intelligence"
        title="Read the signals behind your spending"
        description="Combine AI summaries, model feedback quality, and merchant concentration signals to decide what needs review, retraining, or policy changes next."
      />

      <div className="panel panel-strong">
        <p className="text-xs uppercase tracking-[0.26em] text-slate-500">AI-generated summary</p>
        <h2 className="mt-2 text-2xl font-semibold">Spending intelligence</h2>
        <div className="mt-6 grid gap-4 xl:grid-cols-2">
          {budgetInsights.insights.map((insight) => (
            <div key={insight} className="surface-subtle text-sm">
              {insight}
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Forecast</p>
          <p className="mt-2 text-3xl font-semibold">{inr(budgetInsights.forecast.predicted_amount)}</p>
          <p className="mt-2 text-sm muted">Expected for {budgetInsights.forecast.month}</p>
        </div>
        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Duplicates</p>
          <p className="mt-2 text-3xl font-semibold">{analytics.duplicates.length}</p>
          <p className="mt-2 text-sm muted">Potential duplicate transaction groups</p>
        </div>
        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Subscriptions</p>
          <p className="mt-2 text-3xl font-semibold">{analytics.subscriptions.length}</p>
          <p className="mt-2 text-sm muted">Recurring merchants detected</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Model feedback</p>
              <h3 className="mt-2 text-xl font-semibold">Correction and retraining readiness</h3>
            </div>
            <span className="pill">{feedbackInsights.ready_for_retrain ? "Retrain-ready" : "Collecting"}</span>
          </div>
          <div className="mini-stat-grid">
            <div className="mini-stat">
              <p className="mini-stat-label">Total corrections</p>
              <p className="mini-stat-value">{feedbackInsights.total_feedback}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Last 30 days</p>
              <p className="mini-stat-value">{feedbackInsights.recent_feedback}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Low confidence</p>
              <p className="mini-stat-value">{feedbackInsights.low_confidence_transactions}</p>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {feedbackInsights.guidance.map((item) => (
              <div key={item} className="surface-subtle text-sm">
                {item}
              </div>
            ))}
          </div>

          <div className="mt-5">
            <p className="text-sm font-medium text-white">Top correction patterns</p>
            <div className="mt-3 space-y-3">
              {feedbackInsights.top_corrections.length === 0 && <p className="text-sm muted">No correction history yet.</p>}
              {feedbackInsights.top_corrections.map((item) => (
                <div key={`${item.from_category}-${item.to_category}`} className="surface-subtle">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-slate-100">
                      {item.from_category} <span className="text-slate-500">to</span> {item.to_category}
                    </p>
                    <span className="badge-soft">{item.count} times</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Recent learning signals</p>
          <h3 className="mt-2 text-xl font-semibold">Latest corrections</h3>
          <div className="mt-5 space-y-3">
            {feedbackInsights.recent_items.length === 0 && <p className="text-sm muted">No recent corrections yet.</p>}
            {feedbackInsights.recent_items.map((item, index) => (
              <div key={`${item.transaction_text}-${index}`} className="surface-subtle">
                <p className="text-sm text-slate-100">{item.transaction_text}</p>
                <p className="mt-2 text-sm muted">
                  {item.predicted_category} corrected to {item.corrected_category}
                </p>
                <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                  {new Date(item.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Merchant concentration</p>
              <h3 className="mt-2 text-xl font-semibold">Spend concentration watchlist</h3>
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
            {merchantIntel.watchlist.map((item) => (
              <div key={item} className="surface-subtle text-sm">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Recurring merchants</p>
          <h3 className="mt-2 text-xl font-semibold">Subscription watchlist</h3>
          <div className="mt-5 space-y-3">
            {analytics.subscriptions.length === 0 && <p className="text-sm muted">No subscriptions detected yet.</p>}
            {analytics.subscriptions.map((item) => (
              <div key={`${item.merchant}-${item.recurrence}`} className="surface-subtle">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">{item.merchant}</p>
                    <p className="mt-1 text-sm muted">{item.recurrence}</p>
                  </div>
                  <div className="text-sm font-medium text-slate-100">{inr(item.average_amount)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
