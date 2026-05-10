import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import { EXPENSE_CATEGORIES } from "../constants/categories";
import { getTransactions, submitFeedback } from "../services/api";
import type { Transaction } from "../types/transaction";
import { inr, percent } from "../utils/format";

export default function Transactions() {
  const [rows, setRows] = useState<Transaction[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "amount" | "confidence">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [offset, setOffset] = useState(0);
  const [onlyLowConfidence, setOnlyLowConfidence] = useState(false);
  const [edits, setEdits] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const limit = 20;

  const load = async () => {
    setLoading(true);
    try {
      const data = await getTransactions({
        limit,
        offset,
        search: search || undefined,
        category: category || undefined,
        confidence_lt: onlyLowConfidence ? 0.6 : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setRows(data);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timeout = setTimeout(() => {
      void load();
    }, 250);
    return () => clearTimeout(timeout);
  }, [search, category, sortBy, sortOrder, offset, onlyLowConfidence]);

  const handleSubmit = async (row: Transaction) => {
    const corrected = edits[row.id];
    if (!corrected || corrected === row.category) {
      toast.error("Choose a different category first.");
      return;
    }

    try {
      await submitFeedback({
        transaction_id: row.id,
        transaction_text: row.description,
        predicted_category: row.category,
        corrected_category: corrected,
      });
      toast.success("Correction submitted.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to submit correction.");
    }
  };

  return (
    <section className="space-y-6">
      <div className="panel">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Review queue</p>
            <h2 className="mt-2 text-2xl font-semibold">Transactions and category corrections</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <input className="field" placeholder="Search description or merchant" value={search} onChange={(event) => {
              setOffset(0);
              setSearch(event.target.value);
            }} />
            <select className="field" value={category} onChange={(event) => {
              setOffset(0);
              setCategory(event.target.value);
            }}>
              <option value="">All categories</option>
              {EXPENSE_CATEGORIES.map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
            <select className="field" value={sortBy} onChange={(event) => setSortBy(event.target.value as "date" | "amount" | "confidence")}>
              <option value="date">Sort by date</option>
              <option value="amount">Sort by amount</option>
              <option value="confidence">Sort by confidence</option>
            </select>
            <select className="field" value={sortOrder} onChange={(event) => setSortOrder(event.target.value as "asc" | "desc")}>
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
            <label className="flex items-center gap-3 rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm">
              <input type="checkbox" checked={onlyLowConfidence} onChange={(event) => {
                setOffset(0);
                setOnlyLowConfidence(event.target.checked);
              }} />
              Low confidence only
            </label>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Merchant</th>
                <th>Description</th>
                <th>Category</th>
                <th>Confidence</th>
                <th>Amount</th>
                <th>Correction</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={6} className="text-sm muted">
                    Loading transactions...
                  </td>
                </tr>
              )}
              {!loading && rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-sm muted">
                    No transactions match the current filters.
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <tr key={row.id} className={row.low_confidence ? "bg-amber-300/5" : ""}>
                  <td>
                    <div className="flex items-center gap-3">
                      {row.merchant_logo_url ? (
                        <img src={row.merchant_logo_url} alt={row.merchant} className="h-8 w-8 rounded-full bg-white object-contain p-1" />
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-xs uppercase">{row.merchant.slice(0, 1)}</div>
                      )}
                      <div>
                        <p>{row.merchant}</p>
                        <p className="mt-1 text-xs muted">{row.date}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <p>{row.description}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {row.is_subscription && <span className="rounded-full bg-sky-300/12 px-3 py-1 text-xs text-sky-100">{row.recurrence}</span>}
                      {row.anomaly_flag && <span className="rounded-full bg-rose-300/12 px-3 py-1 text-xs text-rose-100">Anomaly</span>}
                    </div>
                  </td>
                  <td>{row.category}</td>
                  <td>
                    <span className={row.low_confidence ? "text-amber-100" : ""}>{percent(row.prediction_confidence)}</span>
                  </td>
                  <td>{inr(Math.abs(row.amount_inr))}</td>
                  <td>
                    <div className="flex flex-col gap-2">
                      <select
                        className="field py-2"
                        value={edits[row.id] ?? row.category}
                        onChange={(event) => setEdits((current) => ({ ...current, [row.id]: event.target.value }))}
                      >
                        {[...EXPENSE_CATEGORIES, "Uncertain"].map((entry) => (
                          <option key={entry} value={entry}>
                            {entry}
                          </option>
                        ))}
                      </select>
                      <button className="button-secondary px-3 py-2 text-xs" onClick={() => void handleSubmit(row)}>
                        Submit correction
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button className="button-secondary px-3 py-2 text-xs" disabled={offset === 0} onClick={() => setOffset((current) => Math.max(current - limit, 0))}>
            Previous
          </button>
          <p className="text-sm muted">Showing page {Math.floor(offset / limit) + 1}</p>
          <button className="button-secondary px-3 py-2 text-xs" disabled={rows.length < limit} onClick={() => setOffset((current) => current + limit)}>
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
