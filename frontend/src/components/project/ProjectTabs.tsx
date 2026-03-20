import { Link, useLocation } from "react-router";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";

const TABS: { path: string; labelKey: TranslationKey }[] = [
  { path: "", labelKey: "project.overview" },
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
    <div className="mb-6 flex gap-2 border-b border-zinc-200">
      {TABS.map(({ path, labelKey }) => {
        const to = `${base}${path}`;
        const active = pathname === to;
        return (
          <Link
            key={path}
            to={to}
            className={`border-b-2 px-4 py-2.5 text-sm font-semibold transition-all duration-200 ${
              active
                ? "border-indigo-600 text-indigo-600 bg-indigo-50/50"
                : "border-transparent text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50/80"
            }`}
          >
            {t(labelKey)}
          </Link>
        );
      })}
    </div>
  );
}
