import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { ScorePanel } from "../components/project/ScorePanel";
import { ScanHistoryTable } from "../components/project/ScanHistoryTable";
import { NextActions } from "../components/project/NextActions";
import { CampaignTimeline } from "../components/project/CampaignTimeline";
import { ActionFeed } from "../components/project/ActionFeed";
import { useI18n } from "../i18n";

export function ProjectPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data, isLoading, error } = useProjectSummary(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;
  if (!data) return <ErrorAlert message={t("common.projectNotFound")} />;

  const { project, latest, previous, latest_monitoring, is_paused } = data;

  return (
    <div>
      <ProjectHeader project={project} isPaused={is_paused} />
      <ProjectTabs projectId={projectId} />

      {/* Action Feed — the primary "what to do" section */}
      <ActionFeed projectId={projectId} />

      {/* Score Panel — compact summary bar below action feed */}
      <div className="mt-6">
        <ScorePanel latest={latest} previous={previous} latestMonitoring={latest_monitoring} />
      </div>

      <NextActions projectId={projectId} />
      <CampaignTimeline projectId={projectId} />

      {/* Scan history collapsed at the bottom */}
      <details className="mt-8 group">
        <summary className="cursor-pointer text-sm font-semibold text-slate-500 hover:text-slate-700 transition">
          Scan History ▾
        </summary>
        <div className="mt-3">
          <ScanHistoryTable latest={latest} />
        </div>
      </details>
    </div>
  );
}
