import { Link, useLocation } from "react-router";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";

const TABS: { path: string; labelKey: TranslationKey }[] = [
  { path: "", labelKey: "project.overview" },
  { path: "/reports", labelKey: "project.reports" },
  { path: "/brand-kit", labelKey: "project.brandKit" },
  { path: "/performance", labelKey: "project.performance" },
  { path: "/seo", labelKey: "project.seo" },
  { path: "/geo", labelKey: "project.geo" },
  { path: "/serp", labelKey: "project.serp" },
  { path: "/community", labelKey: "project.community" },
  { path: "/graph", labelKey: "project.graph" },
];

export function ProjectTabs({ projectId }: { projectId: number }) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const base = `/projects/${projectId}`;

  return (
    <div className="mb-8 inline-flex items-center p-1 bg-slate-100/80 rounded-xl overflow-x-auto scrollbar-none">
      {TABS.map(({ path, labelKey }) => {
        const to = `${base}${path}`;
        const active = pathname === to;
        return (
          <Link
            key={path}
            to={to}
            className={`whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
              active
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-900 hover:bg-black/[0.02]"
            }`}
          >
            {t(labelKey)}
          </Link>
        );
      })}
    </div>
  );
}
