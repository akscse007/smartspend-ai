import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import { createInstantSavingsEntry, createWishlist, deleteWishlist, getWishlistPlan, listWishlists } from "../services/api";
import type { WishlistCombination, WishlistItem, WishlistPlan } from "../types/transaction";
import { inr } from "../utils/format";

export default function WishlistPlanner() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [plan, setPlan] = useState<WishlistPlan | null>(null);
  const [title, setTitle] = useState("");
  const [targetAmount, setTargetAmount] = useState(5000);
  const [priority, setPriority] = useState(3);
  const [notes, setNotes] = useState("");
  const [instantAmount, setInstantAmount] = useState(1000);
  const [instantNote, setInstantNote] = useState("");
  const [selectedWishlistId, setSelectedWishlistId] = useState<number | "">("");
  const [saving, setSaving] = useState(false);
  const [selectedComboKey, setSelectedComboKey] = useState<string | null>(null);

  const load = async () => {
    try {
      const [wishlistRows, planResponse] = await Promise.all([listWishlists(), getWishlistPlan()]);
      setItems(wishlistRows);
      setPlan(planResponse);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to load wishlist planner.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!plan) {
      return;
    }

    const available = [...plan.immediately_affordable, ...plan.next_cycle_affordable];
    if (available.length === 0) {
      setSelectedComboKey(null);
      return;
    }

    const stillExists = selectedComboKey && available.some((combo) => combo.combo_key === selectedComboKey);
    if (!stillExists) {
      const recommended = available.find((combo) => combo.recommended) || available[0];
      setSelectedComboKey(recommended.combo_key);
    }
  }, [plan, selectedComboKey]);

  const handleCreate = async () => {
    if (!title.trim()) {
      toast.error("Enter a wishlist title.");
      return;
    }

    setSaving(true);
    try {
      await createWishlist({
        title: title.trim(),
        target_amount: Number(targetAmount),
        priority: Number(priority),
        notes: notes.trim() || undefined,
      });
      setTitle("");
      setTargetAmount(5000);
      setPriority(3);
      setNotes("");
      toast.success("Wishlist item added.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to add wishlist item.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (wishlistId: number) => {
    setSaving(true);
    try {
      await deleteWishlist(wishlistId);
      toast.success("Wishlist item removed.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to delete wishlist item.");
    } finally {
      setSaving(false);
    }
  };

  const handleAddInstantSavings = async () => {
    if (Number(instantAmount) <= 0) {
      toast.error("Enter an instant savings amount greater than zero.");
      return;
    }

    setSaving(true);
    try {
      await createInstantSavingsEntry({
        amount: Number(instantAmount),
        note: instantNote.trim() || undefined,
        wishlist_id: selectedWishlistId === "" ? undefined : Number(selectedWishlistId),
      });
      setInstantAmount(1000);
      setInstantNote("");
      toast.success(selectedWishlistId === "" ? "Instant savings recorded." : "Instant savings allocated to wishlist.");
      await load();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to add instant savings.");
    } finally {
      setSaving(false);
    }
  };

  const allCombos = plan ? [...plan.immediately_affordable, ...plan.next_cycle_affordable] : [];
  const selectedCombo = allCombos.find((combo) => combo.combo_key === selectedComboKey) || null;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <div className="panel space-y-5">
        <div>
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Wishlist vault</p>
          <h2 className="text-xl font-semibold">Turn savings into planned purchases</h2>
          <p className="mt-2 text-sm muted">Add wishlist items, track how much has already been saved for each one, and let the planner build combinations from the savings still available.</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <input className="field sm:col-span-2" placeholder="Wishlist title" value={title} onChange={(event) => setTitle(event.target.value)} />
          <input className="field" type="number" min={1} value={targetAmount} onChange={(event) => setTargetAmount(Number(event.target.value))} />
          <select className="field" value={priority} onChange={(event) => setPriority(Number(event.target.value))}>
            {[5, 4, 3, 2, 1].map((value) => (
              <option key={value} value={value}>
                Priority {value}
              </option>
            ))}
          </select>
          <input className="field sm:col-span-2" placeholder="Notes (optional)" value={notes} onChange={(event) => setNotes(event.target.value)} />
        </div>

        <button className="button-primary w-full" disabled={saving} onClick={() => void handleCreate()}>
          Add wishlist item
        </button>

        <div className="space-y-3">
          {items.length === 0 && <p className="text-sm muted">No wishlist items yet. Start with one meaningful purchase or experience.</p>}
          {items.map((item) => (
            <div key={item.id} className="surface-subtle">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-white">{item.title}</p>
                    <span className="pill">P{item.priority}</span>
                  </div>
                  <p className="mt-1 text-sm muted">
                    Target {inr(item.target_amount)} | saved {inr(item.allocated_saved)} | remaining {inr(item.remaining_target)}
                  </p>
                  {item.notes && <p className="mt-2 text-sm text-slate-300">{item.notes}</p>}
                  <div className="mt-3 progress-track">
                    <div className="progress-fill" style={{ width: `${Math.min(item.completion_percentage, 100)}%` }} />
                  </div>
                  <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">{item.completion_percentage.toFixed(0)}% funded</p>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    className="button-secondary px-3 py-2 text-xs"
                    type="button"
                    onClick={() => setSelectedWishlistId(item.id)}
                  >
                    Fund this
                  </button>
                  <button className="button-secondary px-3 py-2 text-xs" disabled={saving} onClick={() => void handleDelete(item.id)}>
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel panel-strong space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-400">Instant savings studio</p>
            <h2 className="text-xl font-semibold text-white">Add savings and test wishlist bundles</h2>
            <p className="mt-2 text-sm text-slate-300">Record real-time savings, direct them into a wishlist, and see which combinations are now feasible with this month&apos;s savings plus the predicted next-month surplus.</p>
          </div>
          {plan && <span className="pill">{plan.current_month} to {plan.next_month}</span>}
        </div>

        {!plan ? (
          <p className="text-sm muted">Loading wishlist combinations...</p>
        ) : (
          <>
            <div className="mini-stat-grid">
              <div className="mini-stat">
                <p className="mini-stat-label">Total savings this month</p>
                <p className="mini-stat-value">{inr(plan.current_month_savings)}</p>
              </div>
              <div className="mini-stat">
                <p className="mini-stat-label">Available now</p>
                <p className="mini-stat-value">{inr(plan.current_month_available_savings)}</p>
              </div>
              <div className="mini-stat">
                <p className="mini-stat-label">Next month forecast</p>
                <p className="mini-stat-value">{inr(plan.predicted_next_month_savings)}</p>
              </div>
              <div className="mini-stat">
                <p className="mini-stat-label">Next-cycle capacity</p>
                <p className="mini-stat-value">{inr(plan.next_cycle_savings_capacity)}</p>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="surface-subtle">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">From transactions</p>
                <p className="mt-2 text-lg font-semibold text-white">{inr(plan.current_month_transaction_savings)}</p>
              </div>
              <div className="surface-subtle">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Instant savings added</p>
                <p className="mt-2 text-lg font-semibold text-white">{inr(plan.current_month_instant_savings)}</p>
              </div>
              <div className="surface-subtle">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Already allocated</p>
                <p className="mt-2 text-lg font-semibold text-white">{inr(plan.current_month_allocated_savings)}</p>
              </div>
              <div className="surface-subtle">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Wishlist items</p>
                <p className="mt-2 text-lg font-semibold text-white">{plan.wishlist_count}</p>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-white/[0.04] p-5">
              <div className="mb-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Add instant savings</p>
                <h3 className="mt-2 text-lg font-semibold text-white">Record extra savings in real time</h3>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <input className="field" type="number" min={1} value={instantAmount} onChange={(event) => setInstantAmount(Number(event.target.value))} />
                <select
                  className="field"
                  value={selectedWishlistId}
                  onChange={(event) => setSelectedWishlistId(event.target.value === "" ? "" : Number(event.target.value))}
                >
                  <option value="">Keep as unallocated savings</option>
                  {items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title}
                    </option>
                  ))}
                </select>
                <input
                  className="field md:col-span-2"
                  placeholder="Note (optional): cashback, side income saved, skipped expense..."
                  value={instantNote}
                  onChange={(event) => setInstantNote(event.target.value)}
                />
              </div>
              <button className="button-primary mt-4 w-full" disabled={saving} onClick={() => void handleAddInstantSavings()}>
                Add instant savings
              </button>
            </div>

            <div className="space-y-2">
              {plan.suggestion_summary.map((entry) => (
                <div key={entry} className="surface-subtle text-sm text-slate-200">
                  {entry}
                </div>
              ))}
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              <CombinationColumn
                title="Affordable now"
                hint="Uses only savings still available this month"
                combos={plan.immediately_affordable}
                selectedComboKey={selectedComboKey}
                onSelect={setSelectedComboKey}
              />
              <CombinationColumn
                title="Affordable by next month"
                hint="Uses current available savings plus predicted next-month surplus"
                combos={plan.next_cycle_affordable}
                selectedComboKey={selectedComboKey}
                onSelect={setSelectedComboKey}
              />
            </div>

            {selectedCombo && (
              <div className="rounded-[24px] border border-emerald-300/20 bg-emerald-300/10 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-emerald-100/70">Selected bundle</p>
                    <h3 className="mt-2 text-lg font-semibold text-emerald-50">
                      {selectedCombo.horizon === "now" ? "Current-month match" : "Next-cycle match"}
                    </h3>
                  </div>
                  {selectedCombo.recommended && <span className="pill">Suggested</span>}
                </div>
                <p className="mt-3 text-sm text-emerald-50/90">{selectedCombo.summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {selectedCombo.items.map((item) => (
                    <span key={item.id} className="badge-soft">
                      {item.title} | need {inr(item.remaining_target)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-white">Recent instant savings</p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">Latest manual savings additions and allocations</p>
              </div>
              {plan.recent_savings_entries.length === 0 && <p className="text-sm muted">No instant savings recorded yet.</p>}
              {plan.recent_savings_entries.map((entry) => (
                <div key={entry.id} className="surface-subtle">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{inr(entry.amount)}</p>
                      <p className="mt-1 text-sm muted">
                        {entry.wishlist_title ? `Allocated to ${entry.wishlist_title}` : "Available for future wishlist allocation"}
                      </p>
                      {entry.note && <p className="mt-2 text-sm text-slate-300">{entry.note}</p>}
                    </div>
                    <span className="pill">{new Date(entry.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function CombinationColumn({
  title,
  hint,
  combos,
  selectedComboKey,
  onSelect,
}: {
  title: string;
  hint: string;
  combos: WishlistCombination[];
  selectedComboKey: string | null;
  onSelect: (comboKey: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <p className="text-sm font-medium text-white">{title}</p>
        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{hint}</p>
      </div>
      {combos.length === 0 && <p className="text-sm muted">No bundles available for this horizon yet.</p>}
      {combos.map((combo) => {
        const selected = combo.combo_key === selectedComboKey;
        return (
          <button
            key={combo.combo_key}
            className={`w-full rounded-[22px] border p-4 text-left transition ${
              selected
                ? "border-emerald-300/50 bg-emerald-300/10"
                : combo.recommended
                  ? "border-sky-300/40 bg-sky-300/10"
                  : "border-white/10 bg-white/5"
            }`}
            type="button"
            onClick={() => onSelect(combo.combo_key)}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium text-white">{inr(combo.total_cost)}</p>
                <p className="mt-1 text-sm muted">{combo.items.length} item bundle | priority {combo.priority_score}</p>
              </div>
              <div className="flex gap-2">
                {combo.recommended && <span className="pill">Suggested</span>}
                {selected && <span className="pill">Selected</span>}
              </div>
            </div>
            <p className="mt-3 text-sm text-slate-300">{combo.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {combo.items.map((item) => (
                <span key={item.id} className="badge-soft">
                  {item.title} ({inr(item.remaining_target)} left)
                </span>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
}
