import { useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  Search,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
} from "lucide-react";
import { useI18n } from "../../i18n";
import { useProject } from "../../hooks/useProject";
import { useGeoAsk, useGeoPlatforms } from "../../hooks/useGeoAsk";
import { ErrorAlert } from "../common/ErrorAlert";
import type {
  GeoAskPlatformResult,
  GeoAskSourceStatus,
  GeoPlatformInfo,
} from "../../api/geo";

const MAX_QUERY_LEN = 500;

interface GeoAskPanelProps {
  projectId: number;
}

export function GeoAskPanel({ projectId }: GeoAskPanelProps) {
  const { t } = useI18n();
  const { data: project } = useProject(projectId);
  const platformsQuery = useGeoPlatforms(projectId);
  const { ask, isPending, error, result } = useGeoAsk(projectId);

  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [initialized, setInitialized] = useState(false);

  const platforms = platformsQuery.data?.platforms ?? [];
  const enabledPlatforms = useMemo(
    () => platforms.filter((p) => p.enabled),
    [platforms],
  );

  // Default-select all enabled platforms once loaded.
  useEffect(() => {
    if (!initialized && enabledPlatforms.length) {
      setSelected(new Set(enabledPlatforms.map((p) => p.name)));
      setInitialized(true);
    }
  }, [enabledPlatforms, initialized]);

  const togglePlatform = (name: string, enabled: boolean) => {
    if (!enabled) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const selectAll = () => {
    setSelected(new Set(enabledPlatforms.map((p) => p.name)));
  };

  const clearAll = () => {
    setSelected(new Set());
  };

  const trimmed = query.trim();
  const tooLong = trimmed.length > MAX_QUERY_LEN;
  const empty = trimmed.length === 0;
  const disabled =
    isPending ||
    empty ||
    tooLong ||
    selected.size === 0 ||
    enabledPlatforms.length === 0;

  const handleSubmit = () => {
    if (disabled) return;
    const allEnabledSelected =
      selected.size === enabledPlatforms.length &&
      enabledPlatforms.every((p) => selected.has(p.name));
    ask({
      query: trimmed,
      platforms: allEnabledSelected ? null : Array.from(selected),
    });
  };

  const brandName = project?.brand_name ?? "";

  return (
    <section className="mb-6 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      {/* Collapsible header */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex w-full items-center justify-between gap-3 border-b border-slate-100 px-5 py-4 text-left transition-colors hover:bg-slate-50"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 text-emerald-600">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              {t("geoAsk.title")}
            </h2>
            <p className="text-xs text-slate-500">{t("geoAsk.subtitle")}</p>
          </div>
        </div>
        {collapsed ? (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {!collapsed && (
        <div className="space-y-5 p-5">
          {/* Query input */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {t("geoAsk.queryLabel")}
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("geoAsk.queryPlaceholder")}
              rows={3}
              maxLength={MAX_QUERY_LEN + 50}
              className="w-full resize-y rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
            />
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
              <span>
                {tooLong && (
                  <span className="text-rose-500">
                    {t("geoAsk.queryTooLong")}
                  </span>
                )}
              </span>
              <span className={tooLong ? "text-rose-500" : ""}>
                {trimmed.length}/{MAX_QUERY_LEN}
              </span>
            </div>
          </div>

          {/* Platform chips */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t("geoAsk.platformsLabel")}
              </label>
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  onClick={selectAll}
                  disabled={enabledPlatforms.length === 0}
                  className="rounded-md px-2 py-0.5 font-medium text-emerald-600 transition-colors hover:bg-emerald-50 disabled:opacity-40"
                >
                  {t("geoAsk.selectAll")}
                </button>
                <span className="text-slate-300">/</span>
                <button
                  type="button"
                  onClick={clearAll}
                  className="rounded-md px-2 py-0.5 font-medium text-slate-500 transition-colors hover:bg-slate-100"
                >
                  {t("geoAsk.clearAll")}
                </button>
              </div>
            </div>
            {platformsQuery.isLoading ? (
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>{t("geoAsk.loadingPlatforms")}</span>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {platforms.map((p) => (
                  <PlatformChip
                    key={p.name}
                    platform={p}
                    selected={selected.has(p.name)}
                    onToggle={() => togglePlatform(p.name, p.enabled)}
                    requiresAuthLabel={(vars) =>
                      t("geoAsk.requiresAuth", { vars })
                    }
                  />
                ))}
              </div>
            )}
          </div>

          {/* Submit */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={disabled}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t("geoAsk.submitting", { count: selected.size })}
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  {t("geoAsk.submit")}
                </>
              )}
            </button>
            {empty && !isPending && (
              <span className="text-xs text-slate-400">
                {t("geoAsk.queryRequired")}
              </span>
            )}
          </div>

          {error && (
            <ErrorAlert
              message={error.message || t("geoAsk.askFailed")}
            />
          )}

          {/* Results */}
          {result && (
            <ResultsSection result={result} brandName={brandName} />
          )}
        </div>
      )}
    </section>
  );
}

function PlatformChip({
  platform,
  selected,
  onToggle,
  requiresAuthLabel,
}: {
  platform: GeoPlatformInfo;
  selected: boolean;
  onToggle: () => void;
  requiresAuthLabel: (vars: string) => string;
}) {
  const disabled = !platform.enabled;
  const title = disabled
    ? requiresAuthLabel(platform.auth_env_vars.join(", ") || "")
    : platform.name;
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      title={title}
      className={[
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all",
        disabled
          ? "cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400"
          : selected
            ? "border-emerald-500 bg-emerald-500 text-white shadow-sm"
            : "border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-emerald-50",
      ].join(" ")}
    >
      {selected && !disabled && <CheckCircle2 className="h-3 w-3" />}
      <span>{platform.name}</span>
    </button>
  );
}

function ResultsSection({
  result,
  brandName,
}: {
  result: import("../../api/geo").GeoAskResponse;
  brandName: string;
}) {
  const { t } = useI18n();
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end gap-2 text-[11px] text-slate-400">
        <Info className="h-3 w-3" />
        <span>
          {t("geoAsk.tookMs", {
            ms: result.total_duration_ms,
            n: result.results.length,
            lang: result.query_lang.toUpperCase(),
          })}
        </span>
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        {result.results.map((r) => (
          <PlatformResultCard
            key={r.platform}
            result={r}
            brandName={brandName}
          />
        ))}
      </div>
    </div>
  );
}

function PlatformResultCard({
  result,
  brandName,
}: {
  result: GeoAskPlatformResult;
  brandName: string;
}) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);
  const status = result.source_status;

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm">
      {/* Header */}
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="truncate text-sm font-semibold text-slate-900">
            {result.platform}
          </h4>
          <p className="text-[11px] text-slate-400">
            {(result.duration_ms / 1000).toFixed(1)}s
          </p>
        </div>
        <StatusBadge status={status} error={result.error} />
      </div>

      {/* Mention badge */}
      <div className="mb-3">
        {result.mentioned ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
            <CheckCircle2 className="h-3 w-3" />
            {t("geoAsk.mentions", {
              count: result.mention_count,
              pct:
                result.position_pct != null
                  ? result.position_pct.toFixed(1)
                  : "—",
            })}
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-500">
            <XCircle className="h-3 w-3" />
            {t("geoAsk.notMentioned")}
          </span>
        )}
      </div>

      {/* Snippet */}
      {result.content_snippet && (
        <div className="space-y-2">
          <div
            className={[
              "rounded-lg bg-slate-50 px-3 py-2 text-[12px] leading-relaxed text-slate-700",
              expanded ? "" : "line-clamp-3",
            ].join(" ")}
            dangerouslySetInnerHTML={{
              __html: highlightBrand(result.content_snippet, brandName, expanded),
            }}
          />
          {result.content_snippet.length > 120 && (
            <button
              type="button"
              onClick={() => setExpanded((e) => !e)}
              className="text-[11px] font-medium text-emerald-600 hover:underline"
            >
              {expanded ? t("geoAsk.collapse") : t("geoAsk.expand")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({
  status,
  error,
}: {
  status: GeoAskSourceStatus;
  error: string | null;
}) {
  const { t } = useI18n();
  if (status === "ok") return null;
  if (status === "empty") {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700">
        <AlertTriangle className="h-3 w-3" />
        {t("geoAsk.status.empty")}
      </span>
    );
  }
  if (status === "blocked") {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-orange-700">
        <AlertTriangle className="h-3 w-3" />
        {t("geoAsk.status.blocked")}
      </span>
    );
  }
  return (
    <span
      title={error ?? undefined}
      className="inline-flex max-w-[180px] shrink-0 items-center gap-1 truncate rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-rose-700"
    >
      <XCircle className="h-3 w-3" />
      {t("geoAsk.status.error", { error: error ?? "" })}
    </span>
  );
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightBrand(
  snippet: string,
  brandName: string,
  expanded: boolean,
): string {
  const safe = escapeHtml(snippet);
  if (!expanded || !brandName.trim()) return safe;
  try {
    const re = new RegExp(`(${escapeRegex(brandName.trim())})`, "gi");
    return safe.replace(
      re,
      '<mark class="rounded bg-emerald-200/70 px-0.5 text-emerald-900">$1</mark>',
    );
  } catch {
    return safe;
  }
}
