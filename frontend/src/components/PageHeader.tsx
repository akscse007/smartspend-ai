import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  badge?: string;
};

export default function PageHeader({ eyebrow, title, description, actions, badge }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <span className="section-kicker">{eyebrow}</span>
          {badge && <span className="pill">{badge}</span>}
        </div>
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 sm:text-base">{description}</p>
        </div>
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}
