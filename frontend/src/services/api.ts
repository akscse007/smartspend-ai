import axios, { type AxiosProgressEvent } from "axios";

import {
  AnalyticsOverview,
  AuthResponse,
  AppNotification,
  Budget,
  BudgetInsights,
  BudgetRecommendation,
  CashflowCalendar,
  CategoryPrediction,
  CategorizeResult,
  FeedbackInsights,
  MerchantIntelligence,
  InstantSavingsEntry,
  SavingsGoal,
  SavingsForecast,
  Transaction,
  UploadResponse,
  UserProfile,
  WishlistItem,
  WishlistPlan,
  WhatIfSimulation,
} from "../types/transaction";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const uploadCsv = async (file: File, onUploadProgress?: (event: AxiosProgressEvent) => void) => {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<UploadResponse>("/upload-csv", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
};

export const registerUser = async (payload: { full_name: string; email: string; password: string }) =>
  (await api.post<AuthResponse>("/auth/register", payload)).data;

export const loginUser = async (payload: { email: string; password: string }) =>
  (await api.post<AuthResponse>("/auth/login", payload)).data;

export const getCurrentUser = async () => (await api.get<UserProfile>("/auth/me")).data;

export const addManualTransaction = async (payload: { date: string; description: string; amount: number }) =>
  (await api.post<Transaction>("/transactions", payload)).data;

export const getTransactions = async (params?: {
  limit?: number;
  offset?: number;
  search?: string;
  category?: string;
  confidence_lt?: number;
  sort_by?: "date" | "amount" | "confidence";
  sort_order?: "asc" | "desc";
}) => (await api.get<Transaction[]>("/transactions", { params })).data;

export const overrideCategory = async (transactionId: number, payload: { new_category: string; reason?: string }) =>
  (await api.patch<Transaction>(`/transactions/${transactionId}/override`, payload)).data;

export const submitFeedback = async (payload: {
  transaction_id?: number;
  transaction_text: string;
  predicted_category: string;
  corrected_category: string;
}) => (await api.post("/feedback", payload)).data;

export const getSummary = async () => (await api.get("/analytics/summary")).data;
export const getCategoryData = async () => (await api.get("/analytics/categories")).data;
export const getMonthlyTrend = async () => (await api.get("/analytics/monthly-trend")).data;
export const getAnalyticsOverview = async () => (await api.get<AnalyticsOverview>("/analytics")).data;
export const getAlerts = async () => (await api.get("/alerts")).data;
export const getBudgetRecommendations = async () =>
  (
    await api.get<{ month: string; recommendations: BudgetRecommendation[]; projected_savings: number }>(
      "/budget/recommendations",
    )
  ).data;
export const getForecast = async () => (await api.get("/forecast")).data;
export const getForecastAdvanced = async () => (await api.get("/analytics/forecast")).data;
export const getSavingsForecast = async () => (await api.get<SavingsForecast>("/analytics/savings-forecast")).data;
export const getHealthScore = async () => (await api.get("/financial-health-score")).data;
export const getAiSummary = async () => (await api.get("/ai-summary")).data;
export const getBudgetInsights = async () => (await api.get<BudgetInsights>("/budget-insights")).data;
export const getCashflowCalendar = async (days = 30) =>
  (await api.get<CashflowCalendar>("/analytics/cashflow-calendar", { params: { days } })).data;
export const getMerchantIntelligence = async () =>
  (await api.get<MerchantIntelligence>("/analytics/merchant-intelligence")).data;
export const getFeedbackInsights = async () =>
  (await api.get<FeedbackInsights>("/analytics/feedback-insights")).data;
export const runWhatIfSimulation = async (payload: { category: string; spend_delta: number; extra_savings: number }) =>
  (await api.post<WhatIfSimulation>("/analytics/what-if", payload)).data;

export const predictCategory = async (description: string, amount = 0) =>
  (await api.post<CategoryPrediction>("/ai/predict-category", { description, amount })).data;

export const categorizeExpense = async (description: string, amount = 0) =>
  (await api.post<CategorizeResult>("/categorize", { description, amount })).data;

export const retrainModel = async (algorithm: "logistic_regression" | "random_forest" | "lstm" = "logistic_regression") =>
  (await api.post("/ai/retrain-model", { algorithm })).data;

export const listBudgets = async (params?: { month?: number; year?: number; limit?: number; offset?: number }) =>
  (await api.get<Budget[]>("/budgets", { params })).data;

export const createBudget = async (payload: {
  category: string;
  monthly_limit: number;
  month: number;
  year: number;
  category_id?: number | null;
}) => (await api.post<Budget>("/budgets", payload)).data;

export const updateBudget = async (
  budgetId: number,
  payload: Partial<{
    category: string;
    monthly_limit: number;
    month: number;
    year: number;
    category_id: number | null;
  }>,
) => (await api.patch<Budget>(`/budgets/${budgetId}`, payload)).data;

export const deleteBudget = async (budgetId: number) => (await api.delete(`/budgets/${budgetId}`)).data;

export const listSavingsGoals = async (params?: { limit?: number; offset?: number }) =>
  (await api.get<SavingsGoal[]>("/savings-goals", { params })).data;

export const createSavingsGoal = async (payload: {
  target_amount: number;
  target_date: string;
  current_saved?: number;
}) => (await api.post<SavingsGoal>("/savings-goals", payload)).data;

export const updateSavingsGoalProgress = async (goalId: number, current_saved: number) =>
  (await api.patch<SavingsGoal>(`/savings-goals/${goalId}/progress`, { current_saved })).data;

export const deleteSavingsGoal = async (goalId: number) => (await api.delete(`/savings-goals/${goalId}`)).data;

export const listWishlists = async (params?: { limit?: number; offset?: number }) =>
  (await api.get<WishlistItem[]>("/wishlists", { params })).data;

export const createWishlist = async (payload: { title: string; target_amount: number; priority?: number; notes?: string | null }) =>
  (await api.post<WishlistItem>("/wishlists", payload)).data;

export const updateWishlist = async (
  wishlistId: number,
  payload: Partial<{ title: string; target_amount: number; priority: number; notes: string | null }>,
) => (await api.patch<WishlistItem>(`/wishlists/${wishlistId}`, payload)).data;

export const deleteWishlist = async (wishlistId: number) => (await api.delete(`/wishlists/${wishlistId}`)).data;

export const getWishlistPlan = async () => (await api.get<WishlistPlan>("/wishlists/recommendations")).data;

export const createInstantSavingsEntry = async (payload: { amount: number; note?: string | null; wishlist_id?: number | null }) =>
  (await api.post<InstantSavingsEntry>("/wishlists/savings-entries", payload)).data;

export const listNotifications = async (params?: { unread_only?: boolean; limit?: number; offset?: number }) =>
  (await api.get<AppNotification[]>("/notifications", { params })).data;

export const markNotificationRead = async (notificationId: number, is_read = true) =>
  (await api.patch<AppNotification>(`/notifications/${notificationId}`, { is_read })).data;

export const getMonthlySummary = async () => (await api.get("/analytics/monthly-summary")).data;
export const getCategoryDistribution = async (params?: { month?: number; year?: number }) =>
  (await api.get("/analytics/category-distribution", { params })).data;
export const getIncomeVsExpense = async () => (await api.get("/analytics/income-vs-expense")).data;
export const getSavingsRate = async () => (await api.get("/analytics/savings-rate")).data;
