type IconName =
  | "analytics"
  | "bell"
  | "budget"
  | "chart"
  | "check"
  | "close"
  | "dashboard"
  | "insights"
  | "logout"
  | "menu"
  | "shield"
  | "sparkles"
  | "target"
  | "transactions"
  | "trending"
  | "upload"
  | "wallet";

type AppIconProps = {
  name: IconName;
  className?: string;
};

const icons: Record<IconName, string[]> = {
  analytics: ["M4 19h16", "M7 16V8", "M12 16V5", "M17 16v-4"],
  bell: ["M15 17H9", "M18 16V11a6 6 0 10-12 0v5l-2 2h16l-2-2Z", "M10 17a2 2 0 104 0"],
  budget: ["M4 7h16", "M6 4h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2Z", "M16 12h.01"],
  chart: ["M4 19h16", "M7 15l3-3 3 2 4-5"],
  check: ["M5 12l4 4L19 6"],
  close: ["M6 6l12 12", "M18 6L6 18"],
  dashboard: ["M4 5h7v6H4z", "M13 5h7v10h-7z", "M4 13h7v6H4z", "M13 17h7v2h-7z"],
  insights: ["M12 3v3", "M18.36 5.64l-2.12 2.12", "M21 12h-3", "M18.36 18.36l-2.12-2.12", "M12 21v-3", "M5.64 18.36l2.12-2.12", "M3 12h3", "M5.64 5.64l2.12 2.12", "M12 8a4 4 0 100 8 4 4 0 000-8Z"],
  logout: ["M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4", "M16 17l5-5-5-5", "M21 12H9"],
  menu: ["M4 7h16", "M4 12h16", "M4 17h16"],
  shield: ["M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3Z", "M9.5 12.5l1.8 1.8 3.2-4.3"],
  sparkles: ["M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z", "M5 17l.8 2.2L8 20l-2.2.8L5 23l-.8-2.2L2 20l2.2-.8L5 17Z", "M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z"],
  target: ["M12 3a9 9 0 109 9", "M12 7a5 5 0 105 5", "M12 11a1 1 0 101 1", "M21 3l-7 7"],
  transactions: ["M6 8h12", "M6 12h8", "M6 16h10", "M4 5h16a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V7a2 2 0 012-2Z"],
  trending: ["M4 16l5-5 4 4 7-7", "M14 8h6v6"],
  upload: ["M12 16V5", "M8 9l4-4 4 4", "M5 19h14"],
  wallet: ["M3 7h18", "M5 4h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2Z", "M17 13h.01"],
};

export default function AppIcon({ name, className = "h-5 w-5" }: AppIconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {icons[name].map((path) => (
        <path key={path} d={path} />
      ))}
    </svg>
  );
}
