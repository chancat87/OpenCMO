import { Link } from "react-router";
import { ExternalLink, Activity, Trash2 } from "lucide-react";
import type { Project } from "../../types";
import { StatusBadge } from "./StatusBadge";
import { useI18n } from "../../i18n";

export function ProjectCard({ project, onDelete }: { project: Project; onDelete?: (id: number) => void }) {
  const { latest } = project;
  const { t } = useI18n();

  return (
    <Link
      to={`/projects/${project.id}`}
      className="group relative block overflow-hidden rounded-[1.25rem] border border-zinc-200/60 bg-white p-5 shadow-sm ring-1 ring-zinc-950/5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-indigo-500/10 hover:border-indigo-200"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      
      <div className="relative mb-5 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 ring-1 ring-indigo-100/50 text-indigo-600">
              <Activity size={16} />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 tracking-tight">{project.brand_name}</h3>
              <p className="flex items-center gap-1 text-[11px] text-zinc-500 transition-colors group-hover:text-indigo-600">
                <span className="truncate">{project.url}</span>
                <ExternalLink size={10} className="shrink-0" />
              </p>
            </div>
          </div>
        </div>
        <div className="ml-3 flex items-center gap-2">
          <span className="shrink-0 rounded-md bg-zinc-100/80 ring-1 ring-zinc-200/50 px-2 py-1 text-[10px] font-semibold tracking-wider text-zinc-600 uppercase">
            {project.category}
          </span>
          {onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete(project.id);
              }}
              title="Delete project"
              className="rounded-lg p-1.5 text-zinc-300 opacity-0 transition-all duration-200 group-hover:opacity-100 hover:!bg-rose-50 hover:!text-rose-500 hover:scale-110 active:scale-95"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="relative grid grid-cols-2 gap-2.5">
        <StatusBadge
          label={t("project.seo")}
          value={latest?.seo?.score != null ? `${Math.round(latest.seo.score * 100)}%` : "—"}
          color={latest?.seo?.score != null && latest.seo.score >= 0.8 ? "green" : "gray"}
        />
        <StatusBadge
          label={t("project.geo")}
          value={latest?.geo?.score != null ? `${latest.geo.score}/100` : "—"}
          color={latest?.geo?.score != null && latest.geo.score >= 60 ? "green" : "gray"}
        />
        <StatusBadge
          label={t("project.community")}
          value={latest?.community?.total_hits != null ? t("projectCard.hits", { count: latest.community.total_hits }) : "—"}
          color={latest?.community?.total_hits ? "blue" : "gray"}
        />
        <StatusBadge
          label={t("project.serp")}
          value={latest?.serp?.length ? t("projectCard.kw", { count: latest.serp.length }) : "—"}
          color={latest?.serp?.length ? "purple" : "gray"}
        />
      </div>
    </Link>
  );
}
