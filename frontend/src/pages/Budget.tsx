import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import WishlistPlanner from "../components/WishlistPlanner";
import { EXPENSE_CATEGORIES } from "../constants/categories";
import {
  createBudget,
  createSavingsGoal,
  getBudgetInsights,
  getBudgetRecommendations,
  listBudgets,
  listSavingsGoals,
  runWhatIfSimulation,
  updateSavingsGoalProgress,
} from "../services/api";
import type { Budget as BudgetItem, BudgetInsights, BudgetRecommendation, SavingsGoal, WhatIfSimulation } from "../types/transaction";
import { inr } from "../utils/format";

export default function Budget() {
  const now = useMemo(() => new Date(), []);
  const [budgetInsights, setBudgetInsights] = useState<BudgetInsights | null>(null);
  const [recommendations, setRecommendations] = useState<{ month: string; recommendations: BudgetRecommendation[]; projected_savings: number } | null>(null);
  const [simulation, setSimulation] = useState<WhatIfSimulation | null>(null);
  const [budgets, setBudgets] = useState<BudgetItem[]>([]);
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [category, setCategory] = useState("Food");
  const [monthlyLimit, setMonthlyLimit] = useState(8000);
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [targetAmount, setTargetAmount] = useState(50000);
  const [targetDate, setTargetDate] = useState(`${now.getFullYear()}-12-31`);
  const [currentSaved, setCurrentSaved] = useState(0);
  const [scenarioCategory, setScenarioCategory] = useState("Food");
  const [spendDelta, setSpendDelta] = useState(-2000);
  const [extraSavings, setExtraSavings] = useState(3000);
  const [saving, setSaving] = useState(false);
  const [simulating, setSimulating] = useState(false);

  const load = async () => {
    try {
      const [insights, budgetRows, goalRows, recommendationRows] = await Promise.all([
        getBudgetInsights(),
        listBudgets(),
        listSavingsGoals(),
        getBudgetRecommendations(),
      ]);
      setBudgetInsights(insights);
      setBudgets(budgetRows);
      setGoals(goalRows);
      setRecommendations(recommendationRows);
      if (insights.budgets.length > 0) {
        setScenarioCategory((current) => current || insights.budgets[0].category);
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to load budget planner.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    const targetCategory = scenarioCategory || budgetInsights?.overview.top_category || "Food";
    if (!budgetInsights || !targetCategory) {
      return;
    }

    const run = async () => {
      setSimulating(true);
      try {
        const next = await runWhatIfSimulation({
          category: targetCategory,
          spend_delta: spendDelta,
          extra_savings: extraSavings,
        });
        setSimulation(next);
      } catch (error: any) {
        toast.error(error?.response?.data?.detail || "Failed to calculate scenario.");
      } finally {
        setSimulating(false);
      }
    };

    void run();
  }, [budgetInsights, scenarioCategory, spendDelta, extraSavings]);

  const handleCreateBudget = async () => {
    setSaving(true);
    try {
      await createBudget({
        category,
        monthly_limit: Number(monthlyLimit),
        month: Number(month),
        year: Number(year),
      });
      toast.success("Budget saved.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Budget creation failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateGoal = async () => {
    setSaving(true);
    try {
      await createSavingsGoal({
        target_amount: Number(targetAmount),
        target_date: targetDate,
        current_saved: Number(currentSaved),
      });
      toast.success("Savings goal created.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Goal creation failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleProgress = async (goal: SavingsGoal, amount: number) => {
    setSaving(true);
    try {
      await updateSavingsGoalProgress(goal.id, goal.current_saved + amount);
      toast.success("Savings progress updated.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Progress update failed.");
    } finally {
      setSaving(false);
    }
  };

  if (!budgetInsights) {
    return <div className="panel">Loading budget planner...</div>;
  }

  const behavioral = budgetInsights.behavioral_forecast;

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Planning"
        title="Plan next month before the money moves"
        description="Create budgets and savings goals, test category changes before they happen, and use autopilot recommendations to turn recurring overspend into savings."
        badge={budgetInsights.overview.month}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Budgeted" value={inr(budgetInsights.overview.monthly_budget)} hint="Configured monthly envelope" icon="budget" tone="primary" />
        <MetricCard label="Spent" value={inr(budgetInsights.overview.total_spending)} hint="Current month outflow" icon="wallet" />
        <MetricCard label="Remaining" value={inr(budgetInsights.overview.remaining_budget)} hint="Budget runway left" icon="target" tone="success" />
        <MetricCard
          label="Next month savings"
          value={inr(budgetInsights.savings_forecast.predicted_next_month_savings)}
          hint={`Projected surplus for ${budgetInsights.savings_forecast.next_month}`}
          icon="trending"
          tone="warning"
        />
      </div>

      {budgetInsights.alerts.length > 0 && (
        <div className="panel border-amber-300/20 bg-amber-300/10">
          <p className="text-xs uppercase tracking-[0.26em] text-amber-50/70">Budget alerts</p>
          <div className="mt-3 space-y-2 text-sm text-amber-50">
            {budgetInsights.alerts.map((alert) => (
              <div key={alert}>{alert}</div>
            ))}
          </div>
        </div>
      )}

      <div className="panel border-sky-300/20 bg-sky-300/10 text-sm text-sky-50">
        Budget and savings threshold alerts are also emailed to the address you use to sign in when SMTP is configured on the backend.
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Set budget</p>
            <h2 className="text-xl font-semibold">Category budget planner</h2>
          </div>
          <select className="field" value={category} onChange={(event) => setCategory(event.target.value)}>
            {EXPENSE_CATEGORIES.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
          <input className="field" type="number" value={monthlyLimit} onChange={(event) => setMonthlyLimit(Number(event.target.value))} />
          <div className="grid grid-cols-2 gap-3">
            <input className="field" type="number" value={month} min={1} max={12} onChange={(event) => setMonth(Number(event.target.value))} />
            <input className="field" type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} />
          </div>
          <button className="button-primary w-full" disabled={saving} onClick={() => void handleCreateBudget()}>
            Save monthly budget
          </button>
        </div>

        <div className="panel space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Savings goal</p>
            <h2 className="text-xl font-semibold">Target-based planner</h2>
          </div>
          <input className="field" type="number" value={targetAmount} onChange={(event) => setTargetAmount(Number(event.target.value))} />
          <input className="field" type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} />
          <input className="field" type="number" value={currentSaved} onChange={(event) => setCurrentSaved(Number(event.target.value))} />
          <button className="button-primary w-full" disabled={saving} onClick={() => void handleCreateGoal()}>
            Save savings goal
          </button>
        </div>
      </div>

      <WishlistPlanner />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Budget autopilot</p>
              <h2 className="text-xl font-semibold">Recommended budget resets</h2>
            </div>
            {recommendations && <span className="pill">{recommendations.month}</span>}
          </div>
          <div className="mini-stat-grid">
            <div className="mini-stat">
              <p className="mini-stat-label">Recommendations</p>
              <p className="mini-stat-value">{recommendations?.recommendations.length || 0}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Projected savings</p>
              <p className="mini-stat-value">{inr(recommendations?.projected_savings || 0)}</p>
            </div>
            <div className="mini-stat">
              <p className="mini-stat-label">Best target</p>
              <p className="mini-stat-value">
                {recommendations?.recommendations[0]?.category || "None"}
              </p>
            </div>
          </div>
          <div className="mt-5 space-y-3">
            {!recommendations || recommendations.recommendations.length === 0 ? (
              <p className="text-sm muted">Autopilot will appear after more spending history is available.</p>
            ) : (
              recommendations.recommendations.map((item) => (
                <div key={item.category} className="surface-subtle">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{item.category}</p>
                      <p className="mt-1 text-sm muted">
                        Current {inr(item.current_spend)} | suggested cap {inr(item.recommended_budget)}
                      </p>
                    </div>
                    <span className="badge-soft">{inr(item.potential_savings)} saved</span>
                  </div>
                  <p className="mt-3 text-sm text-slate-300">{item.advice}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="scenario-card space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-400">What-if simulator</p>
            <h2 className="text-xl font-semibold text-white">Pressure-test your month</h2>
            <p className="mt-2 text-sm text-slate-300">Model how one category cut and extra savings allocation changes the month before you commit.</p>
          </div>
          <div className="space-y-4">
            <select className="field" value={scenarioCategory} onChange={(event) => setScenarioCategory(event.target.value)}>
              {[...new Set([
                ...budgetInsights.budgets.map((item) => item.category),
                ...EXPENSE_CATEGORIES,
              ])].map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm text-slate-300">Category spend adjustment</label>
                <span className="badge-soft">{spendDelta >= 0 ? "+" : ""}{inr(spendDelta)}</span>
              </div>
              <input className="slider" type="range" min={-10000} max={10000} step={500} value={spendDelta} onChange={(event) => setSpendDelta(Number(event.target.value))} />
              <div className="mt-3 flex flex-wrap gap-2">
                {[-5000, -2500, 0, 2500].map((value) => (
                  <button key={value} className="button-secondary px-3 py-2 text-xs" type="button" onClick={() => setSpendDelta(value)}>
                    {value > 0 ? "+" : ""}{inr(value)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm text-slate-300">Extra savings to set aside</label>
                <span className="badge-soft">{inr(extraSavings)}</span>
              </div>
              <input className="slider" type="range" min={0} max={15000} step={500} value={extraSavings} onChange={(event) => setExtraSavings(Number(event.target.value))} />
            </div>
          </div>

          {simulating && <p className="text-sm muted">Calculating scenario...</p>}
          {simulation && (
            <>
              <div className="mini-stat-grid">
                <div className="mini-stat">
                  <p className="mini-stat-label">Adjusted spend</p>
                  <p className="mini-stat-value">{inr(simulation.adjusted_total_spend)}</p>
                </div>
                <div className="mini-stat">
                  <p className="mini-stat-label">Remaining budget</p>
                  <p className="mini-stat-value">{inr(simulation.adjusted_remaining_budget)}</p>
                </div>
                <div className="mini-stat">
                  <p className="mini-stat-label">Savings impact</p>
                  <p className="mini-stat-value">{inr(simulation.savings_impact)}</p>
                </div>
              </div>
              <div className="space-y-3">
                {simulation.summary.map((item) => (
                  <div key={item} className="surface-subtle text-sm">
                    {item}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="panel panel-strong">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Behavioral budget forecasting</p>
            <h2 className="text-xl font-semibold">Expected spending by month end</h2>
            <p className="mt-2 text-sm muted">
              Predictive pacing based on observed daily spending in {behavioral.month} through {new Date(behavioral.anchor_date).toLocaleDateString()}.
            </p>
          </div>
          <span className="pill">{behavioral.month}</span>
        </div>

        <div className="mini-stat-grid">
          <div className="mini-stat">
            <p className="mini-stat-label">Daily average</p>
            <p className="mini-stat-value">{inr(behavioral.daily_average_spend)}</p>
          </div>
          <div className="mini-stat">
            <p className="mini-stat-label">Projected month end</p>
            <p className="mini-stat-value">{inr(behavioral.projected_month_end_spend)}</p>
          </div>
          <div className="mini-stat">
            <p className="mini-stat-label">Remaining days</p>
            <p className="mini-stat-value">{behavioral.remaining_days}</p>
          </div>
        </div>

        <div className="mt-5 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-3">
            {behavioral.summary.map((item) => (
              <div key={item} className="surface-subtle text-sm">
                {item}
              </div>
            ))}
            {behavioral.alerts.length > 0 && (
              <div className="rounded-[22px] border border-amber-300/20 bg-amber-300/10 p-4">
                <p className="text-sm font-medium text-amber-100">Predictive alerts</p>
                <div className="mt-3 space-y-2 text-sm text-amber-50">
                  {behavioral.alerts.map((item) => (
                    <div key={item}>{item}</div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {behavioral.categories.length === 0 && <p className="text-sm muted">Create category budgets to unlock per-category forecasting.</p>}
            {behavioral.categories.map((item) => (
              <div key={item.category} className="surface-subtle">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{item.category}</p>
                    <p className="mt-1 text-sm muted">
                      Run rate {inr(item.daily_run_rate)}/day | projected {inr(item.projected_spend)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${item.projected_overrun > 0 ? "text-amber-200" : "text-slate-100"}`}>
                      {item.projected_overrun > 0 ? `${inr(item.projected_overrun)} over` : "On track"}
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {item.days_to_exceed === null ? "No exceedance predicted" : item.days_to_exceed === 0 ? "Already exceeded" : `Exceeds in ${item.days_to_exceed} days`}
                    </p>
                  </div>
                </div>
                <div className="mt-3 progress-track">
                  <div className="progress-fill" style={{ width: `${Math.min(item.pace_ratio, 100)}%` }} />
                </div>
                <p className="mt-2 text-sm muted">
                  Current {inr(item.current_spend)} of {inr(item.budget_limit)} | remaining {inr(item.remaining_budget)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="mb-4">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Utilization</p>
          <h2 className="text-xl font-semibold">Budget progress</h2>
        </div>
        <div className="space-y-4">
          {budgetInsights.budgets.length === 0 && <p className="text-sm muted">No category budgets configured yet.</p>}
          {budgetInsights.budgets.map((item) => (
            <div key={item.category} className="surface-subtle">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-white">{item.category}</p>
                  <p className="mt-1 text-sm muted">
                    {inr(item.spent)} of {inr(item.limit)}
                  </p>
                </div>
                <div className={item.exceeded ? "text-rose-200" : "text-slate-100"}>{item.percentage_used.toFixed(1)}%</div>
              </div>
              <div className="mt-3 progress-track">
                <div className="progress-fill" style={{ width: `${Math.min(item.percentage_used, 100)}%` }} />
              </div>
              <p className="mt-2 text-sm muted">Remaining {inr(item.remaining)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Budgets</p>
            <h2 className="text-xl font-semibold">Saved budgets</h2>
          </div>
          <div className="space-y-3">
            {budgets.length === 0 && <p className="text-sm muted">No budgets created yet.</p>}
            {budgets.map((budget) => (
              <div key={budget.id} className="surface-subtle">
                <p className="font-medium text-white">
                  {budget.category} | {String(budget.month).padStart(2, "0")}/{budget.year}
                </p>
                <p className="mt-1 text-sm muted">
                  {inr(budget.total_spent_per_category)} spent | {inr(budget.remaining_budget)} remaining
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Savings goals</p>
            <h2 className="text-xl font-semibold">Progress tracker</h2>
          </div>
          <div className="space-y-3">
            {goals.length === 0 && <p className="text-sm muted">No savings goals created yet.</p>}
            {goals.map((goal) => (
              <div key={goal.id} className="surface-subtle">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{inr(goal.target_amount)} target</p>
                    <p className="mt-1 text-sm muted">Due {goal.target_date}</p>
                  </div>
                  <span className="pill">{goal.completion_percentage.toFixed(0)}%</span>
                </div>
                <div className="mt-3 progress-track">
                  <div className="progress-fill" style={{ width: `${Math.min(goal.completion_percentage, 100)}%` }} />
                </div>
                <div className="mt-3 flex gap-2">
                  <button className="button-secondary px-3 py-2 text-xs" disabled={saving} onClick={() => void handleProgress(goal, 1000)}>
                    +1000
                  </button>
                  <button className="button-secondary px-3 py-2 text-xs" disabled={saving} onClick={() => void handleProgress(goal, 5000)}>
                    +5000
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
