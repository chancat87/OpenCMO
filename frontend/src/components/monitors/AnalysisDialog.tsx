import { useEffect, useMemo } from "react";
import {
  X,
  Search,
  BarChart3,
  MessageCircle,
  Target,
  Bot,
  Loader2,
  CheckCircle,
  Radar,
  TriangleAlert,
  Lightbulb,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import {
  useTaskArtifacts,
  useTaskPoll,
  useTaskFindings,
  useTaskRecommendations,
  useTaskStale,
} from "../../hooks/useTasks";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import type {
  AnalysisProgress,
  Finding,
  Recommendation,
  TaskArtifactCluster,
  TaskArtifactOpportunity,
  TaskArtifactStageCard,
} from "../../types";

const STAGE_CONFIG: Record<string, { icon: typeof Search; labelKey: TranslationKey }> = {
  context_build: { icon: Search, labelKey: "analysis.stageContextBuild" },
  signal_collect: { icon: Radar, labelKey: "analysis.stageSignalCollect" },
  signal_normalize: { icon: Bot, labelKey: "analysis.stageSignalNormalize" },
  domain_review: { icon: MessageCircle, labelKey: "analysis.stageDomainReview" },
  strategy_synthesis: { icon: Target, labelKey: "analysis.stageStrategySynthesis" },
  persist_publish: { icon: CheckCircle, labelKey: "analysis.stagePersistPublish" },
};

const STATUS_STYLE: Record<string, string> = {
  started: "bg-slate-50 text-slate-600 ring-slate-200",
  running: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  failed: "bg-rose-50 text-rose-700 ring-rose-200",
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
};

const SEVERITY_STYLE: Record<string, string> = {
  critical: "bg-rose-50 text-rose-700 ring-rose-200",
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
  info: "bg-slate-50 text-slate-600 ring-slate-200",
};

const PRIORITY_STYLE: Record<string, string> = {
  high: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  medium: "bg-sky-50 text-sky-700 ring-sky-200",
  low: "bg-slate-50 text-slate-600 ring-slate-200",
};

function getAnalystEvents(progress: AnalysisProgress[]) {
  return progress.filter((item) => item.stage === "domain_review" && item.agent);
}

function EvidenceRefs({
  refs,
  label,
}: {
  refs: Finding["evidence_refs"];
  label: string;
}) {
  if (!refs?.length) return null;

  return (
    <div className="mt-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </p>
      <div className="flex flex-wrap gap-2">
        {refs.slice(0, 4).map((ref, index) => {
          const content = (
            <>
              <span className="font-medium text-slate-500">{ref.source}</span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-700">{ref.key}</span>
              <span className="text-slate-400">=</span>
              <span className="font-medium text-slate-900">{ref.value}</span>
            </>
          );

          if (ref.url) {
            return (
              <a
                key={`${ref.source}-${ref.key}-${index}`}
                href={ref.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs ring-1 ring-inset ring-slate-200 transition-colors hover:bg-slate-50"
              >
                {content}
                <ExternalLink size={12} className="text-slate-400" />
              </a>
            );
          }

          return (
            <div
              key={`${ref.source}-${ref.key}-${index}`}
              className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs ring-1 ring-inset ring-slate-200"
            >
              {content}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FindingCard({
  finding,
  evidenceLabel,
}: {
  finding: Finding;
  evidenceLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {finding.domain}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            SEVERITY_STYLE[finding.severity] ?? SEVERITY_STYLE.info
          }`}
        >
          {finding.severity}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{finding.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{finding.summary}</p>
      <EvidenceRefs refs={finding.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function RecommendationCard({
  recommendation,
  evidenceLabel,
  rationaleLabel,
}: {
  recommendation: Recommendation;
  evidenceLabel: string;
  rationaleLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-indigo-500">
          {recommendation.owner_type}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            PRIORITY_STYLE[recommendation.priority] ?? PRIORITY_STYLE.low
          }`}
        >
          {recommendation.priority}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{recommendation.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{recommendation.summary}</p>
      {recommendation.rationale ? (
        <p className="mt-3 text-xs leading-relaxed text-indigo-900/80">
          <span className="font-semibold">{rationaleLabel}: </span>
          {recommendation.rationale}
        </p>
      ) : null}
      <EvidenceRefs refs={recommendation.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function OpportunityCard({
  opportunity,
  evidenceLabel,
  actionLabel,
}: {
  opportunity: TaskArtifactOpportunity;
  evidenceLabel: string;
  actionLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-sky-100 bg-sky-50/70 p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-sky-600">
          {opportunity.type.replaceAll("_", " ")}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            PRIORITY_STYLE[opportunity.priority] ?? PRIORITY_STYLE.low
          }`}
        >
          {opportunity.priority}
        </span>
        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-500 ring-1 ring-inset ring-slate-200">
          {opportunity.score}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{opportunity.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{opportunity.summary}</p>
      <p className="mt-3 text-xs leading-relaxed text-sky-900/80">
        <span className="font-semibold">{actionLabel}: </span>
        {opportunity.recommended_action}
      </p>
      <EvidenceRefs refs={opportunity.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function ClusterCard({
  cluster,
  gapsLabel,
  quickWinsLabel,
}: {
  cluster: TaskArtifactCluster;
  gapsLabel: string;
  quickWinsLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{cluster.name}</span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-600">
          {cluster.opportunity_score}
        </span>
      </div>
      <p className="text-xs text-slate-500">
        {cluster.brand_keyword_count} brand · {cluster.competitor_keyword_count} competitor
      </p>
      {cluster.gap_keywords.length ? (
        <div className="mt-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {gapsLabel}
          </p>
          <div className="flex flex-wrap gap-2">
            {cluster.gap_keywords.map((keyword) => (
              <span
                key={`${cluster.name}-${keyword}`}
                className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {cluster.quick_win_keywords.length ? (
        <div className="mt-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {quickWinsLabel}
          </p>
          <div className="flex flex-wrap gap-2">
            {cluster.quick_win_keywords.map((keyword) => (
              <span
                key={`${cluster.name}-qw-${keyword}`}
                className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SummaryMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl bg-white/80 p-4 ring-1 ring-inset ring-white/70">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
    </div>
  );
}

function StageCard({
  card,
  label,
}: {
  card: TaskArtifactStageCard;
  label: string;
}) {
  const cfg = STAGE_CONFIG[card.stage] ?? STAGE_CONFIG.context_build!;
  const Icon = cfg.icon;
  const style = STATUS_STYLE[card.status] ?? STATUS_STYLE.started;

  return (
    <div className={`rounded-xl p-4 ring-1 ring-inset ${style}`}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon size={14} />
          <span className="text-xs font-semibold">{label}</span>
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-wider opacity-80">
          {card.status}
        </span>
      </div>
      <p className="text-sm leading-relaxed">{card.summary}</p>
    </div>
  );
}

export function AnalysisDialog({
  taskId,
  url,
  onClose,
}: {
  taskId: string;
  url: string;
  onClose: () => void;
}) {
  const { data: task } = useTaskPoll(taskId);
  const { data: artifacts } = useTaskArtifacts(taskId, !!taskId);
  const { t } = useI18n();

  const progress: AnalysisProgress[] = task?.progress ?? [];
  const isDone = task?.status === "completed" || task?.status === "failed";
  const isStale = useTaskStale(task?.status, progress.length);
  const analystEvents = useMemo(() => getAnalystEvents(progress), [progress]);
  const stageCards = artifacts?.stage_cards ?? [];
  const issues = artifacts?.issues ?? [];
  const topOpportunities = artifacts?.opportunities?.top ?? [];
  const topClusters = artifacts?.cluster_summary?.top_clusters ?? [];

  const { data: findings = [] } = useTaskFindings(taskId, isDone);
  const { data: recommendations = [] } = useTaskRecommendations(taskId, isDone);

  useEffect(() => {
    const el = document.getElementById("analysis-scroll");
    if (el) el.scrollTop = el.scrollHeight;
  }, [progress.length, findings.length, recommendations.length, issues.length, topOpportunities.length, topClusters.length]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="flex h-[82vh] w-full max-w-4xl flex-col rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{t("analysis.title")}</h2>
            <p className="mt-0.5 max-w-xl truncate text-xs text-slate-400">{url}</p>
            <p className="mt-0.5 text-xs text-slate-400">{t("analysis.backgroundHint")}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div id="analysis-scroll" className="flex-1 space-y-6 overflow-y-auto px-6 py-4">
          {progress.length === 0 && !isDone && !isStale && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Loader2 size={32} className="mb-3 animate-spin text-indigo-400" />
              <p className="text-sm text-slate-400">{t("analysis.initializing")}</p>
            </div>
          )}

          {isStale && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <TriangleAlert size={32} className="mb-3 text-amber-500" />
              <p className="text-sm font-medium text-amber-600">{t("analysis.taskStale")}</p>
            </div>
          )}

          {isDone && artifacts?.overview ? (
            <section className="overflow-hidden rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.16),_transparent_38%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 ring-1 ring-indigo-200/70">
                  <Sparkles size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-indigo-500">
                    {t("analysis.summaryTitle")}
                  </p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                    {artifacts.overview.headline}
                  </h3>
                  <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
                    {t("analysis.summarySubtitle")}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <SummaryMetric
                  label={t("analysis.keyFindings")}
                  value={artifacts.overview.findings_count}
                />
                <SummaryMetric
                  label={t("analysis.recommendedActions")}
                  value={artifacts.overview.recommendations_count}
                />
                <SummaryMetric
                  label={t("analysis.focusAreas")}
                  value={artifacts.overview.focus_domains.length || "—"}
                />
              </div>

              <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-2xl bg-white/80 p-4 ring-1 ring-inset ring-slate-200/70">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {t("analysis.focusAreas")}
                  </p>
                  {artifacts.overview.focus_domains.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {artifacts.overview.focus_domains.map((domain) => (
                        <span
                          key={domain}
                          className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700"
                        >
                          {domain}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">{t("analysis.focusPending")}</p>
                  )}
                </div>

                {artifacts.brief.top_recommendations[0] ? (
                  <div className="rounded-2xl bg-indigo-950 p-4 text-white shadow-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-200">
                      {t("analysis.nextBestAction")}
                    </p>
                    <p className="mt-3 text-sm font-semibold leading-relaxed">
                      {artifacts.brief.top_recommendations[0].title}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-indigo-100/90">
                      {artifacts.brief.top_recommendations[0].summary}
                    </p>
                  </div>
                ) : topOpportunities[0] ? (
                  <div className="rounded-2xl bg-sky-950 p-4 text-white shadow-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-200">
                      {t("analysis.nextBestAction")}
                    </p>
                    <p className="mt-3 text-sm font-semibold leading-relaxed">
                      {topOpportunities[0].title}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-sky-100/90">
                      {topOpportunities[0].summary}
                    </p>
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}

          {isDone && topOpportunities.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={14} className="text-sky-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.opportunities")}
                </h3>
              </div>
              <div className="space-y-3">
                {topOpportunities.map((opportunity, index) => (
                  <OpportunityCard
                    key={`${opportunity.type}-${opportunity.title}-${index}`}
                    opportunity={opportunity}
                    evidenceLabel={t("analysis.evidence")}
                    actionLabel={t("analysis.recommendedMove")}
                  />
                ))}
              </div>
            </section>
          )}

          {isDone && topClusters.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Target size={14} className="text-slate-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.clusterGaps")}
                </h3>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {topClusters.map((cluster) => (
                  <ClusterCard
                    key={cluster.name}
                    cluster={cluster}
                    gapsLabel={t("analysis.gapKeywords")}
                    quickWinsLabel={t("analysis.quickWinKeywords")}
                  />
                ))}
              </div>
            </section>
          )}

          {issues.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <TriangleAlert size={14} className="text-amber-500" />
                <h3 className="text-sm font-semibold text-slate-900">{t("analysis.watchouts")}</h3>
              </div>
              <div className="space-y-3">
                {issues.map((issue, index) => {
                  const labelKey = STAGE_CONFIG[issue.stage]?.labelKey;
                  return (
                    <div
                      key={`${issue.stage}-${index}`}
                      className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4"
                    >
                      <div className="mb-1 flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-amber-700">
                          {labelKey ? t(labelKey) : issue.stage}
                        </span>
                        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700 ring-1 ring-inset ring-amber-200">
                          {issue.status}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-900">{issue.summary}</p>
                      <p className="mt-2 text-sm leading-relaxed text-slate-700">{issue.resolution}</p>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {stageCards.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  {t("analysis.workflowStages")}
                </span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {stageCards.map((card) => {
                  const labelKey = STAGE_CONFIG[card.stage]?.labelKey;
                  return (
                    <StageCard
                      key={card.stage}
                      card={card}
                      label={labelKey ? t(labelKey) : card.stage}
                    />
                  );
                })}
              </div>
            </section>
          )}

          {analystEvents.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  {t("analysis.domainReviews")}
                </span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <div className="space-y-3">
                {analystEvents.map((item, index) => (
                  <div
                    key={`${item.agent}-${index}`}
                    className="rounded-xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200"
                  >
                    <div className="mb-1.5 flex items-center gap-2">
                      <BarChart3 size={14} className="text-slate-500" />
                      <span className="text-xs font-semibold text-slate-700">{item.agent}</span>
                    </div>
                    <p className="text-sm leading-relaxed text-slate-700">
                      {item.detail ?? item.summary ?? item.content}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {isDone && findings.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <TriangleAlert size={14} className="text-rose-500" />
                <h3 className="text-sm font-semibold text-slate-900">{t("analysis.keyFindings")}</h3>
              </div>
              <div className="space-y-3">
                {findings.map((finding, index) => (
                  <FindingCard
                    key={`${finding.domain}-${finding.title}-${index}`}
                    finding={finding}
                    evidenceLabel={t("analysis.evidence")}
                  />
                ))}
              </div>
            </section>
          )}

          {isDone && recommendations.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Lightbulb size={14} className="text-amber-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.recommendedActions")}
                </h3>
              </div>
              <div className="space-y-3">
                {recommendations.map((recommendation, index) => (
                  <RecommendationCard
                    key={`${recommendation.domain}-${recommendation.title}-${index}`}
                    recommendation={recommendation}
                    evidenceLabel={t("analysis.evidence")}
                    rationaleLabel={t("analysis.rationale")}
                  />
                ))}
              </div>
            </section>
          )}

          {isDone && findings.length === 0 && recommendations.length === 0 && (
            <p className="py-8 text-center text-sm text-slate-400">{t("analysis.noRecordedFindings")}</p>
          )}

          {task?.summary && !isDone && (
            <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700 ring-1 ring-inset ring-slate-200">
              {task.summary}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 px-6 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {isDone ? (
              <>
                <CheckCircle
                  size={14}
                  className={task?.status === "failed" ? "text-rose-500" : "text-emerald-500"}
                />
                <span className={task?.status === "failed" ? "text-rose-600" : "text-emerald-600"}>
                  {task?.status === "failed" ? t("analysis.workflowFailed") : t("analysis.workflowComplete")}
                </span>
              </>
            ) : isStale ? (
              <>
                <TriangleAlert size={14} className="text-amber-500" />
                <span className="text-amber-600">{t("analysis.taskStale")}</span>
              </>
            ) : (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>
                  {stageCards.length}
                  {" / 6 "}
                  {t("analysis.stages")}
                </span>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
          >
            {isDone ? t("analysis.close") : t("analysis.closeBackground")}
          </button>
        </div>
      </div>
    </div>
  );
}
