import { useState } from "react";
import { Link } from "react-router";
import { motion } from "framer-motion";
import { useProjects, useDeleteProject } from "../hooks/useProjects";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { AnimatedPage } from "../components/common/AnimatedPage";
import { SkeletonCard } from "../components/common/SkeletonCard";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { SetupBanner } from "../components/dashboard/SetupBanner";
import { WelcomeHero } from "../components/dashboard/WelcomeHero";
import { SettingsDialog } from "../components/settings/SettingsDialog";
import { useI18n } from "../i18n";
import { Plus } from "lucide-react";

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.06,
      duration: 0.45,
      ease: [0.25, 0.46, 0.45, 0.94] as const,
    },
  }),
};

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const { t } = useI18n();
  const [showSettings, setShowSettings] = useState(false);
  const deleteError =
    deleteProject.error instanceof Error
      ? deleteProject.error.message
      : deleteProject.isError
        ? "Failed to delete project."
        : null;

  if (isLoading) {
    return (
      <AnimatedPage>
        <div className="mb-10">
          <div className="h-8 w-48 rounded-lg bg-slate-100 animate-pulse mb-2" />
          <div className="h-4 w-72 rounded bg-slate-50 animate-pulse" />
        </div>
        <SkeletonCard count={3} />
      </AnimatedPage>
    );
  }
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <AnimatedPage>
      <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t("dashboard.title")}</h1>
          <p className="text-[15px] text-slate-500 mt-1.5">{t("dashboard.subtitle")}</p>
        </div>
        <Link
          to="/monitors"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-slate-800 hover:shadow-md active:scale-95"
        >
          <Plus size={16} />
          {t("dashboard.newMonitor")}
        </Link>
      </div>
      <SetupBanner onOpenSettings={() => setShowSettings(true)} />
      {deleteError ? <div className="mb-6"><ErrorAlert message={deleteError} /></div> : null}
      <InsightBanner />
      <GlobalOverview />
      {!projects?.length ? (
        <WelcomeHero />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p, i) => (
            <motion.div
              key={p.id}
              custom={i}
              variants={cardVariants}
              initial="hidden"
              animate="visible"
              whileHover={{
                y: -4,
                transition: { duration: 0.2, ease: "easeOut" },
              }}
            >
              <ProjectCard
                project={p}
                onDelete={(id) => {
                  if (window.confirm(t("dashboard.deleteConfirm"))) {
                    deleteProject.mutate(id);
                  }
                }}
              />
            </motion.div>
          ))}
        </div>
      )}
      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </AnimatedPage>
  );
}
