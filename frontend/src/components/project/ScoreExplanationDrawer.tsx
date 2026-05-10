import { X } from "lucide-react";
import type { ChartData, LatestScans } from "../../types";
import { useI18n } from "../../i18n";

export type ScoreExplanationKind = "seo" | "geo";

type PreviousScores = {
  seo?: {
    scanned_at: string;
    score: number | null;
    performance_score?: number | null;
    health_score?: number | null;
  };
  geo?: { scanned_at: string; score: number };
} | null;

function latestSeriesValue(chart: ChartData | undefined, key: string): number | null {
  const series = chart?.[key];
  if (!Array.isArray(series) || series.length === 0) return null;
  const value = series[series.length - 1];
  return typeof value === "number" ? value : null;
}

function normalizePercent(value: number | null | undefined): number | null {
  if (value == null) return null;
  return Math.round(value <= 1 ? value * 100 : value);
}

function rounded(value: number | null | undefined): number | null {
  if (value == null) return null;
  return Math.round(value);
}

function signed(value: number): string {
  if (value > 0) return `+${value}`;
  return String(value);
}

function formatValue(value: number | null, max: number): string | null {
  if (value == null) return null;
  return `${value}/${max}`;
}

function getDelta(current: number | null, previous: number | null): number | null {
  if (current == null || previous == null) return null;
  return current - previous;
}

function DetailRow({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <p className="text-sm font-semibold text-slate-900">{label}</p>
        <p className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
          {value}
        </p>
      </div>
      {note ? <p className="mt-2 text-sm leading-6 text-slate-600">{note}</p> : null}
    </div>
  );
}

export function ScoreExplanationDrawer({
  open,
  kind,
  latest,
  previous,
  seoChart,
  geoChart,
  onClose,
}: {
  open: boolean;
  kind: ScoreExplanationKind | null;
  latest: LatestScans;
  previous?: PreviousScores;
  seoChart?: ChartData;
  geoChart?: ChartData;
  onClose: () => void;
}) {
  const { t } = useI18n();

  if (!open || !kind) return null;

  const isSeo = kind === "seo";
  const title = isSeo ? t("score.seoScore") : t("score.geoScore");
  const current = isSeo
    ? normalizePercent(latest.seo?.score ?? latestSeriesValue(seoChart, "performance"))
    : rounded(latest.geo?.score ?? latestSeriesValue(geoChart, "geo_score"));
  const prev = isSeo
    ? normalizePercent(previous?.seo?.score)
    : rounded(previous?.geo?.score);
  const delta = getDelta(current, prev);

  const pagespeed = normalizePercent(
    latest.seo?.performance_score ?? latestSeriesValue(seoChart, "pagespeed_performance"),
  );
  const seoHealth = normalizePercent(
    latest.seo?.health_score ?? latestSeriesValue(seoChart, "health"),
  );
  const geoVisibility = rounded(latestSeriesValue(geoChart, "visibility"));
  const geoPosition = rounded(latestSeriesValue(geoChart, "position"));
  const geoSentiment = rounded(latestSeriesValue(geoChart, "sentiment"));

  const rows = isSeo
    ? [
        {
          label: t("score.seoPagespeedPerformance"),
          value: formatValue(pagespeed, 100) ?? t("score.dataUnavailable"),
          note: t("score.seoPerformanceFallback"),
        },
        {
          label: t("score.seoHealthScore"),
          value: formatValue(seoHealth, 100) ?? t("score.dataUnavailable"),
          note: t("score.seoFormula"),
        },
        {
          label: t("score.seoTechnicalFoundation"),
          value: t("score.points", { value: 40 }),
        },
        {
          label: t("score.seoOnPageQuality"),
          value: t("score.points", { value: 30 }),
        },
        {
          label: t("score.seoPagePerformance"),
          value: t("score.points", { value: 30 }),
        },
      ]
    : [
        {
          label: t("score.geoVisibilityFormula"),
          value: formatValue(geoVisibility, 40) ?? t("score.dataUnavailable"),
        },
        {
          label: t("score.geoPositionFormula"),
          value: formatValue(geoPosition, 30) ?? t("score.dataUnavailable"),
        },
        {
          label: t("score.geoSentimentFormula"),
          value: formatValue(geoSentiment, 30) ?? t("score.dataUnavailable"),
          note: geoSentiment == null ? t("score.geoSentimentMissing") : undefined,
        },
      ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-end bg-slate-950/40 p-0 backdrop-blur-sm sm:items-center sm:justify-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={t("score.explanationTitle", { name: title })}
      onClick={onClose}
    >
      <div
        className="max-h-[92vh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl sm:max-w-2xl sm:rounded-3xl sm:p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              {t("score.explain")}
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              {t("score.explanationTitle", { name: title })}
            </h2>
          </div>
          <button
            type="button"
            title={t("common.cancel")}
            aria-label={t("common.cancel")}
            onClick={onClose}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
          >
            <X size={17} />
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200/80 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              {t("score.current")}
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {current != null ? `${current}/100` : t("score.dataUnavailable")}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              {t("score.previous")}
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {prev != null ? `${prev}/100` : t("score.dataUnavailable")}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              {t("score.changedBy")}
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">
              {delta != null ? t("score.points", { value: signed(delta) }) : t("score.dataUnavailable")}
            </p>
          </div>
        </div>

        <div className="mt-5 rounded-2xl border border-slate-200/80 bg-white p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {t("score.formula")}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {isSeo ? t("score.seoFormula") : t("score.geoFormula")}
          </p>
        </div>

        <div className="mt-4 space-y-3">
          {rows.map((row) => (
            <DetailRow key={row.label} {...row} />
          ))}
        </div>
      </div>
    </div>
  );
}
