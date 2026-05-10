import type { UserProfile } from "../types/transaction";

type NavbarProps = {
  user: UserProfile | null;
  onLogout: () => void;
};

export default function Navbar({ user, onLogout }: NavbarProps) {
  const now = new Date();

  return (
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[#071015]/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 lg:px-6">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-[#8cf0d8]">Smart Budget Planner</p>
          <h1 className="text-xl font-semibold text-slate-50">AI expense categorization cockpit</h1>
        </div>
        <div className="hidden items-center gap-3 md:flex">
          <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-right">
            <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Today</p>
            <p className="text-sm text-slate-200">{now.toLocaleDateString()}</p>
          </div>
          {user && (
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2">
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">User</p>
              <p className="text-sm text-slate-200">{user.full_name}</p>
            </div>
          )}
          <span className="pill">Hybrid ML + Rules</span>
          {user && (
            <button className="button-secondary px-3 py-2 text-xs" onClick={onLogout}>
              Logout
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
