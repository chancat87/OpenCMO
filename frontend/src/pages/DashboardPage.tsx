import { Link } from "react-router";
import { useProjects, useDeleteProject } from "../hooks/useProjects";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { useI18n } from "../i18n";
import { Plus } from "lucide-react";

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{t("dashboard.title")}</h1>
          <p className="text-sm text-zinc-500 mt-1">Overview of your AI marketing campaigns</p>
        </div>
        <Link
          to="/monitors"
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:scale-[1.02] hover:shadow-indigo-600/30 active:scale-95"
        >
          <Plus size={16} className="text-indigo-100" />
          {t("dashboard.newMonitor")}
        </Link>
      </div>
      {!projects?.length ? (
        <EmptyState
          title={t("dashboard.noProjects")}
          description={t("dashboard.noProjectsDesc")}
          action={
            <Link
              to="/monitors"
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:scale-[1.02] active:scale-95"
            >
              <Plus size={16} />
              {t("dashboard.createMonitor")}
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onDelete={(id) => deleteProject.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
