export type Transaction = {
  id: number;
  date: string;
  description: string;
  merchant: string;
  amount: number;
  currency: string;
  amount_inr: number;
  category: string;
  prediction_confidence: number;
  is_income: boolean;
  is_subscription: boolean;
  anomaly_flag: boolean;
  recurrence: string;
  merchant_logo_url?: string | null;
  low_confidence?: boolean;
};

export type AlertItem = {
  message: string;
  severity: "low" | "medium" | "high";
};

export type BudgetRecommendation = {
  category: string;
  current_spend: number;
  recommended_budget: number;
  potential_savings: number;
  advice: string;
};

export type CashflowEvent = {
  date: string;
  title: string;
  amount: number;
  type: "income" | "expense" | "goal" | "budget" | string;
  cadence?: string | null;
  note?: string | null;
};

export type CashflowCalendar = {
  anchor_date: string;
  window_days: number;
  expected_income: number;
  expected_expense: number;
  expected_net: number;
  events: CashflowEvent[];
};

export type MerchantInsightItem = {
  merchant: string;
  total_spend: number;
  transaction_count: number;
  average_ticket: number;
  share_of_spend: number;
  last_seen: string;
};

export type MerchantIntelligence = {
  month: string;
  total_spend: number;
  concentration_share: number;
  repeat_merchant_share: number;
  top_merchants: MerchantInsightItem[];
  watchlist: string[];
};

export type WhatIfSimulation = {
  month: string;
  category: string;
  current_category_spend: number;
  adjusted_category_spend: number;
  current_total_spend: number;
  adjusted_total_spend: number;
  current_remaining_budget: number;
  adjusted_remaining_budget: number;
  forecast_adjusted: number;
  savings_impact: number;
  summary: string[];
};

export type FeedbackCorrection = {
  from_category: string;
  to_category: string;
  count: number;
};

export type FeedbackRecentItem = {
  transaction_text: string;
  predicted_category: string;
  corrected_category: string;
  timestamp: string;
};

export type FeedbackInsights = {
  total_feedback: number;
  recent_feedback: number;
  low_confidence_transactions: number;
  corrected_transactions: number;
  ready_for_retrain: boolean;
  top_corrections: FeedbackCorrection[];
  recent_items: FeedbackRecentItem[];
  guidance: string[];
};

export type Budget = {
  id: number;
  user_id: number;
  category: string;
  category_id: number | null;
  monthly_limit: number;
  month: number;
  year: number;
  total_spent_per_category: number;
  remaining_budget: number;
  percentage_used: number;
  overspending_flag: boolean;
};

export type SavingsGoal = {
  id: number;
  user_id: number;
  target_amount: number;
  target_date: string;
  current_saved: number;
  completion_percentage: number;
  months_remaining: number | null;
};

export type WishlistItem = {
  id: number;
  user_id: number;
  title: string;
  target_amount: number;
  priority: number;
  notes?: string | null;
  allocated_saved: number;
  remaining_target: number;
  completion_percentage: number;
  created_at: string;
  updated_at: string;
};

export type InstantSavingsEntry = {
  id: number;
  user_id: number;
  wishlist_id?: number | null;
  wishlist_title?: string | null;
  amount: number;
  note?: string | null;
  created_at: string;
};

export type SavingsForecast = {
  current_month: string;
  current_month_income: number;
  current_month_expense: number;
  current_month_savings: number;
  next_month: string;
  predicted_next_month_income: number;
  predicted_next_month_expense: number;
  predicted_next_month_savings: number;
};

export type WishlistCombination = {
  combo_key: string;
  horizon: "now" | "next_cycle" | string;
  items: {
    id: number;
    title: string;
    target_amount: number;
    priority: number;
    notes?: string | null;
    allocated_saved: number;
    remaining_target: number;
    completion_percentage: number;
  }[];
  total_cost: number;
  remaining_savings: number;
  utilization: number;
  priority_score: number;
  recommended: boolean;
  summary: string;
};

export type WishlistPlan = {
  current_month: string;
  next_month: string;
  current_month_savings: number;
  current_month_transaction_savings: number;
  current_month_instant_savings: number;
  current_month_allocated_savings: number;
  current_month_available_savings: number;
  predicted_next_month_savings: number;
  next_cycle_savings_capacity: number;
  wishlist_count: number;
  considered_wishlist_count: number;
  immediately_affordable: WishlistCombination[];
  next_cycle_affordable: WishlistCombination[];
  recent_savings_entries: InstantSavingsEntry[];
  suggestion_summary: string[];
};

export type AppNotification = {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type CategoryPrediction = {
  category: string;
  confidence: number;
  merchant: string;
  merchant_logo_url?: string | null;
  model_source: string;
};

export type CategorizeResult = {
  description: string;
  predicted_category: string;
  confidence: number;
  merchant: string;
  merchant_logo_url?: string | null;
  model_source: string;
};

export type AnalyticsOverview = {
  overview: {
    month: string;
    total_spending: number;
    monthly_budget: number;
    top_category: string;
    remaining_budget: number;
  };
  category_distribution: { category: string; amount: number }[];
  monthly_category_spending: { month: string; category: string; amount: number }[];
  forecast: {
    month: string;
    predicted_amount: number;
    confidence_interval?: [number, number] | null;
  };
  duplicates: { description: string; amount: number; count: number }[];
  subscriptions: { merchant: string; recurrence: string; average_amount: number }[];
  insights: string[];
};

export type BudgetInsights = {
  overview: {
    month: string;
    total_spending: number;
    monthly_budget: number;
    top_category: string;
    remaining_budget: number;
  };
  budgets: {
    category: string;
    limit: number;
    spent: number;
    remaining: number;
    percentage_used: number;
    exceeded: boolean;
  }[];
  alerts: string[];
  forecast: {
    month: string;
    predicted_amount: number;
    confidence_interval?: [number, number] | null;
  };
  savings_forecast: SavingsForecast;
  behavioral_forecast: {
    month: string;
    anchor_date: string;
    elapsed_days: number;
    remaining_days: number;
    daily_average_spend: number;
    current_total_spend: number;
    projected_month_end_spend: number;
    categories: {
      category: string;
      current_spend: number;
      daily_run_rate: number;
      projected_spend: number;
      budget_limit: number;
      remaining_budget: number;
      projected_overrun: number;
      days_to_exceed: number | null;
      pace_ratio: number;
    }[];
    alerts: string[];
    summary: string[];
  };
  monthly_category_spending: { month: string; category: string; amount: number }[];
  subscriptions: { merchant: string; recurrence: string; average_amount: number }[];
  duplicates: { description: string; amount: number; count: number }[];
  insights: string[];
};

export type UploadResponse = {
  inserted_count: number;
  duplicate_count: number;
  transactions: Transaction[];
};

export type UserProfile = {
  id: number;
  full_name: string;
  email: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: UserProfile;
};
