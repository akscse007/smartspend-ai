import { useMemo, useState, type FormEvent } from "react";
import toast from "react-hot-toast";

import { addManualTransaction, retrainModel, uploadCsv } from "../services/api";
import type { Transaction } from "../types/transaction";
import { inr, percent } from "../utils/format";

type PreviewRow = {
  Date: string;
  Description: string;
  Amount: string;
};

type ManualFormState = {
  date: string;
  description: string;
  amount: string;
  entryType: "expense" | "income";
};

const REQUIRED_COLUMNS = ["Date", "Description", "Amount"];

const createInitialManualForm = (): ManualFormState => ({
  date: new Date().toISOString().slice(0, 10),
  description: "",
  amount: "",
  entryType: "expense",
});

function parsePreview(text: string): PreviewRow[] {
  const [headerLine, ...body] = text.split(/\r?\n/).filter(Boolean);
  if (!headerLine) {
    return [];
  }

  const headers = headerLine.split(",").map((item) => item.trim());
  return body.slice(0, 8).map((line) => {
    const values = line.split(",").map((item) => item.trim());
    return headers.reduce(
      (acc, header, index) => ({ ...acc, [header]: values[index] || "" }),
      {} as PreviewRow,
    );
  });
}

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<PreviewRow[]>([]);
  const [missingColumns, setMissingColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<Transaction[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [retraining, setRetraining] = useState<"idle" | "logistic_regression" | "random_forest" | "lstm">("idle");
  const [dragActive, setDragActive] = useState(false);
  const [manualForm, setManualForm] = useState<ManualFormState>(createInitialManualForm);
  const [manualSubmitting, setManualSubmitting] = useState(false);

  const isValid = useMemo(() => missingColumns.length === 0 && !!file, [missingColumns.length, file]);
  const hasManualDraft = useMemo(
    () => Boolean(manualForm.date && manualForm.description.trim() && manualForm.amount.trim()),
    [manualForm.amount, manualForm.date, manualForm.description],
  );

  const handleFile = async (nextFile: File | null) => {
    setFile(nextFile);
    setRows([]);
    setUploadProgress(0);

    if (!nextFile) {
      setPreviewRows([]);
      setMissingColumns([]);
      return;
    }

    const text = await nextFile.text();
    const [headerLine = ""] = text.split(/\r?\n/);
    const headers = headerLine.split(",").map((item) => item.trim());
    setMissingColumns(REQUIRED_COLUMNS.filter((column) => !headers.includes(column)));
    setPreviewRows(parsePreview(text));
  };

  const handleUpload = async () => {
    if (!file || !isValid) {
      toast.error("Choose a valid CSV with Date, Description and Amount columns.");
      return;
    }

    setUploading(true);
    try {
      const response = await uploadCsv(file, (event) => {
        const total = event.total || file.size;
        const loaded = event.loaded || 0;
        setUploadProgress(Math.round((loaded / total) * 100));
      });
      setRows(response.transactions);
      toast.success(`Imported ${response.inserted_count} transactions. Duplicates skipped: ${response.duplicate_count}.`);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const description = manualForm.description.trim();
    const amount = Number(manualForm.amount);

    if (!manualForm.date || description.length < 2 || !Number.isFinite(amount) || amount <= 0) {
      toast.error("Enter a date, description, and amount greater than zero.");
      return;
    }

    setManualSubmitting(true);
    try {
      const normalizedAmount = manualForm.entryType === "income" ? -amount : amount;
      const transaction = await addManualTransaction({
        date: manualForm.date,
        description,
        amount: normalizedAmount,
      });

      setRows((current) => [transaction, ...current]);
      setManualForm(createInitialManualForm());
      toast.success("Transaction added and categorized.");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Could not add the transaction.");
    } finally {
      setManualSubmitting(false);
    }
  };

  const handleRetrain = async (algorithm: "logistic_regression" | "random_forest" | "lstm") => {
    setRetraining(algorithm);
    try {
      const result = await retrainModel(algorithm);
      toast.success(`Retrained ${result.trained_samples} samples with ${result.text_embedding_backend}.`);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Retraining failed.");
    } finally {
      setRetraining("idle");
    }
  };

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="panel panel-strong">
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">CSV intake</p>
          <h2 className="mt-2 text-2xl font-semibold">Drag, validate, upload</h2>
          <p className="mt-2 max-w-xl text-sm muted">
            Upload bank or wallet exports with `Date`, `Description`, and `Amount`. The app previews rows before import,
            validates columns, flags duplicates, and stores model confidence.
          </p>

          <label
            className={[
              "mt-6 flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed px-6 py-8 text-center transition",
              dragActive ? "border-emerald-300/60 bg-emerald-300/10" : "border-white/15 bg-white/[0.03]",
            ].join(" ")}
            onDragEnter={() => setDragActive(true)}
            onDragLeave={() => setDragActive(false)}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              void handleFile(event.dataTransfer.files?.[0] || null);
            }}
          >
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(event) => {
                void handleFile(event.target.files?.[0] || null);
              }}
            />
            <p className="text-lg font-medium">{file ? file.name : "Drop CSV here or click to browse"}</p>
            <p className="mt-2 max-w-sm text-sm muted">Required columns: Date, Description, Amount</p>
            <p className="mt-2 text-sm muted">Max preview: first 8 rows</p>
          </label>

          {missingColumns.length > 0 && (
            <div className="mt-4 rounded-[22px] border border-rose-300/20 bg-rose-300/10 p-4 text-sm text-rose-100">
              Missing required columns: {missingColumns.join(", ")}
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <button className="button-primary" disabled={!isValid || uploading} onClick={handleUpload}>
              {uploading ? `Uploading ${uploadProgress}%` : "Upload and categorize"}
            </button>
            <button
              className="button-secondary"
              disabled={retraining !== "idle"}
              onClick={() => void handleRetrain("logistic_regression")}
            >
              {retraining === "logistic_regression" ? "Retraining..." : "Retrain logistic model"}
            </button>
            <button
              className="button-secondary"
              disabled={retraining !== "idle"}
              onClick={() => void handleRetrain("random_forest")}
            >
              {retraining === "random_forest" ? "Retraining..." : "Retrain random forest"}
            </button>
            <button
              className="button-secondary"
              disabled={retraining !== "idle"}
              onClick={() => void handleRetrain("lstm")}
            >
              {retraining === "lstm" ? "Retraining..." : "Retrain LSTM model"}
            </button>
          </div>

          <div className="mt-4 progress-track">
            <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="panel">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Manual entry</p>
            <h3 className="mt-2 text-xl font-semibold">Add one transaction</h3>
            <p className="mt-2 text-sm muted">
              Add a single expense or income without changing the CSV upload flow. The transaction is categorized the same way after save.
            </p>

            <form className="mt-5 space-y-4" onSubmit={(event) => void handleManualSubmit(event)}>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-2 text-sm">
                  <span className="muted">Date</span>
                  <input
                    type="date"
                    className="field"
                    value={manualForm.date}
                    onChange={(event) => setManualForm((current) => ({ ...current, date: event.target.value }))}
                    required
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="muted">Type</span>
                  <select
                    className="field"
                    value={manualForm.entryType}
                    onChange={(event) =>
                      setManualForm((current) => ({
                        ...current,
                        entryType: event.target.value as ManualFormState["entryType"],
                      }))
                    }
                  >
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </label>
              </div>

              <label className="block space-y-2 text-sm">
                <span className="muted">Description</span>
                <input
                  type="text"
                  className="field"
                  placeholder="e.g. Zomato order, salary credit, metro recharge"
                  value={manualForm.description}
                  onChange={(event) => setManualForm((current) => ({ ...current, description: event.target.value }))}
                  maxLength={300}
                  required
                />
              </label>

              <label className="block space-y-2 text-sm">
                <span className="muted">Amount</span>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  className="field"
                  placeholder="0.00"
                  value={manualForm.amount}
                  onChange={(event) => setManualForm((current) => ({ ...current, amount: event.target.value }))}
                  required
                />
              </label>

              <div className="flex flex-wrap gap-3">
                <button className="button-primary" type="submit" disabled={manualSubmitting}>
                  {manualSubmitting ? "Saving..." : "Add transaction"}
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={!hasManualDraft || manualSubmitting}
                  onClick={() => setManualForm(createInitialManualForm())}
                >
                  Reset form
                </button>
              </div>

              <p className="text-xs muted">
                Choose income or expense and enter a positive amount. Income is stored automatically with the right sign.
              </p>
            </form>
          </div>

          <div className="panel">
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Preview</p>
            <h3 className="mt-2 text-xl font-semibold">Column validation</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {REQUIRED_COLUMNS.map((column) => (
                <span
                  key={column}
                  className={[
                    "rounded-full px-3 py-1 text-xs font-medium",
                    missingColumns.includes(column) ? "bg-rose-300/12 text-rose-200" : "bg-emerald-300/12 text-emerald-100",
                  ].join(" ")}
                >
                  {column}
                </span>
              ))}
            </div>
            <div className="mt-5 space-y-3">
              {previewRows.length === 0 && <p className="text-sm muted">No CSV preview available yet.</p>}
              {previewRows.map((row, index) => (
                <div key={`${row.Description}-${index}`} className="rounded-[20px] border border-white/10 bg-white/[0.03] p-4 text-sm">
                  <p className="font-medium">{row.Description}</p>
                  <p className="mt-1 muted">
                    {row.Date} | {row.Amount}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-slate-500">Latest result</p>
            <h3 className="text-xl font-semibold">Categorized transactions</h3>
          </div>
          {rows.length > 0 && <span className="pill">{rows.length} rows</span>}
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Category</th>
                <th>Confidence</th>
                <th>Signals</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-sm muted">
                    Upload a CSV or add a manual transaction to see categorized results here.
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <tr key={row.id} className={row.low_confidence ? "bg-amber-200/5" : ""}>
                  <td>{row.date}</td>
                  <td>
                    <p>{row.description}</p>
                    <p className="mt-1 text-xs muted">{row.merchant}</p>
                  </td>
                  <td>{row.category}</td>
                  <td>{percent(row.prediction_confidence)}</td>
                  <td>
                    <div className="flex flex-wrap gap-2">
                      {row.low_confidence && <span className="rounded-full bg-amber-300/12 px-3 py-1 text-xs text-amber-100">Low confidence</span>}
                      {row.anomaly_flag && <span className="rounded-full bg-rose-300/12 px-3 py-1 text-xs text-rose-100">Anomaly</span>}
                      {row.is_subscription && <span className="rounded-full bg-sky-300/12 px-3 py-1 text-xs text-sky-100">{row.recurrence}</span>}
                    </div>
                  </td>
                  <td>{inr(Math.abs(row.amount_inr))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
