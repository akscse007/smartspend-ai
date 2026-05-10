import { useState } from "react";
import toast from "react-hot-toast";

import { loginUser, registerUser } from "../services/api";
import type { UserProfile } from "../types/transaction";

type AuthPageProps = {
  onAuthenticated: (token: string, user: UserProfile) => void;
};

type ApiValidationIssue = {
  msg?: string;
};

const getAuthErrorMessage = (error: any) => {
  if (error?.code === "ERR_NETWORK") {
    return "Cannot reach the backend API. Start the backend on http://localhost:8001 using backend/.venv.";
  }
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue: ApiValidationIssue) => issue?.msg?.trim())
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) {
      return messages.join(" ");
    }
  }
  if (typeof error?.message === "string" && error.message.trim()) {
    return error.message;
  }
  return "Authentication failed.";
};

export default function Auth({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    const trimmedFullName = fullName.trim();
    const trimmedEmail = email.trim().toLowerCase();

    if (mode === "register" && trimmedFullName.length < 2) {
      toast.error("Full name must be at least 2 characters.");
      return;
    }
    if (trimmedEmail.length < 5) {
      toast.error("Enter a valid email address.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const response =
        mode === "login"
          ? await loginUser({ email: trimmedEmail, password })
          : await registerUser({ full_name: trimmedFullName, email: trimmedEmail, password });

      localStorage.setItem("auth_token", response.access_token);
      localStorage.setItem("auth_user", JSON.stringify(response.user));
      onAuthenticated(response.access_token, response.user);
      toast.success(mode === "login" ? "Logged in." : "Account created.");
    } catch (error: any) {
      toast.error(getAuthErrorMessage(error), { id: "auth-error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel panel-strong flex flex-col justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-[#8cf0d8]">Smart Budget Planner</p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight">Private finance workspace for every user.</h1>
            <p className="mt-4 max-w-xl text-sm muted">
              Register once, sign in from the dashboard, and keep uploads, budgets, alerts, corrections, and insights isolated per account.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm">JWT-based login</div>
            <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm">Per-user budgets and analytics</div>
            <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4 text-sm">Feedback and corrections stay scoped</div>
          </div>
        </div>

        <div className="panel">
          <div className="flex gap-2 rounded-[20px] border border-white/10 bg-white/[0.03] p-2">
            <button
              className={`flex-1 rounded-2xl px-4 py-3 text-sm font-medium ${mode === "login" ? "bg-emerald-300/12 text-emerald-100" : "text-slate-400"}`}
              onClick={() => setMode("login")}
            >
              Login
            </button>
            <button
              className={`flex-1 rounded-2xl px-4 py-3 text-sm font-medium ${mode === "register" ? "bg-emerald-300/12 text-emerald-100" : "text-slate-400"}`}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>

          <div className="mt-6 space-y-4">
            {mode === "register" && (
              <input className="field" placeholder="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
            )}
            <input className="field" placeholder="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <input className="field" placeholder="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <button className="button-primary w-full" disabled={loading} onClick={() => void handleSubmit()}>
              {loading ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
