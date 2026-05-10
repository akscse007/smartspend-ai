import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import toast from "react-hot-toast";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Analytics from "./pages/Analytics";
import Auth from "./pages/Auth";
import Budget from "./pages/Budget";
import Dashboard from "./pages/Dashboard";
import Insights from "./pages/Insights";
import Transactions from "./pages/Transactions";
import Upload from "./pages/Upload";
import { getCurrentUser } from "./services/api";
import type { UserProfile } from "./types/transaction";

function readStoredUser(): UserProfile | null {
  const raw = localStorage.getItem("auth_user");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export default function App() {
  const [user, setUser] = useState<UserProfile | null>(() => readStoredUser());
  const [checkingSession, setCheckingSession] = useState<boolean>(() => !!localStorage.getItem("auth_token"));

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      setCheckingSession(false);
      return;
    }

    const verify = async () => {
      try {
        const me = await getCurrentUser();
        localStorage.setItem("auth_user", JSON.stringify(me));
        setUser(me);
      } catch {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
        setUser(null);
        toast.error("Session expired. Please log in again.");
      } finally {
        setCheckingSession(false);
      }
    };

    void verify();
  }, []);

  const handleAuthenticated = (_token: string, nextUser: UserProfile) => {
    setUser(nextUser);
    setCheckingSession(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    setUser(null);
    toast.success("Logged out.");
  };

  if (checkingSession) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-300">Checking session...</div>;
  }

  if (!user) {
    return <Auth onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="min-h-screen">
      <Navbar user={user} onLogout={handleLogout} />
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 lg:grid-cols-[250px_1fr] lg:px-6">
        <Sidebar />
        <main className="space-y-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/budget" element={<Budget />} />
            <Route path="/insights" element={<Insights />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
