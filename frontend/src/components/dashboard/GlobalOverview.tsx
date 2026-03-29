import { useQuery } from "@tanstack/react-query";
import { apiJson } from "../../api/client";
import { useI18n } from "../../i18n";
import {
  Search, Globe, Users, Hash, GitBranch, Rocket,
} from "lucide-react";

interface OverviewData {
  project_count: number;
  avg_seo_score: number | null;
  avg_geo_score: number | null;
  total_community_hits: number;
  total_keywords: number;
  total_competitors: number;
  recent_campaigns: Array<{
    id: number;
    goal: string;
    brand_name: string;
    status: string;
    channels: string[];
    created_at: string;
  }>;
}

function useOverview() {
  return useQuery<OverviewData>({
    queryKey: ["overview"],
    queryFn: () => apiJson<OverviewData>("/overview"),
    refetchInterval: 60_000,
  });
}

function MetricCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-zinc-100 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${color}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="text-2xl font-bold text-zinc-800">
          {value ?? "—"}
        </div>
        <div className="text-xs text-zinc-500">{label}</div>
      </div>
    </div>
  );
}

function seoColor(score: number | null): string {
  if (score == null) return "bg-slate-50 text-slate-400";
  if (score >= 90) return "bg-emerald-50 text-emerald-600";
  if (score >= 50) return "bg-amber-50 text-amber-600";
  return "bg-rose-50 text-rose-600";
}

function geoColor(score: number | null): string {
  if (score == null) return "bg-slate-50 text-slate-400";
  if (score >= 60) return "bg-emerald-50 text-emerald-600";
  if (score >= 30) return "bg-amber-50 text-amber-600";
  return "bg-rose-50 text-rose-600";
}

function communityColor(hits: number): string {
  if (hits > 0) return "bg-blue-50 text-blue-600";
  return "bg-slate-50 text-slate-400";
}

export function GlobalOverview() {
  const { data } = useOverview();
  const { t } = useI18n();

  if (!data || data.project_count === 0) return null;

  return (
    <div className="mb-8">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          icon={Search}
          label={t("overview.avgSeo")}
          value={data.avg_seo_score ? `${data.avg_seo_score}%` : null}
          color={seoColor(data.avg_seo_score)}
        />
        <MetricCard
          icon={Globe}
          label={t("overview.avgGeo")}
          value={data.avg_geo_score ? `${data.avg_geo_score}/100` : null}
          color={geoColor(data.avg_geo_score)}
        />
        <MetricCard
          icon={Users}
          label={t("overview.communityHits")}
          value={data.total_community_hits}
          color={communityColor(data.total_community_hits)}
        />
        <MetricCard
          icon={Hash}
          label={t("overview.keywords")}
          value={data.total_keywords}
          color="bg-indigo-50 text-indigo-600"
        />
        <MetricCard
          icon={GitBranch}
          label={t("overview.competitors")}
          value={data.total_competitors}
          color="bg-rose-50 text-rose-600"
        />
        <MetricCard
          icon={Rocket}
          label={t("overview.campaigns")}
          value={data.recent_campaigns.length}
          color="bg-purple-50 text-purple-600"
        />
      </div>
    </div>
  );
}
