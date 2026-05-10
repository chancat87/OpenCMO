import { apiJson } from "./client";
import type { Locale } from "../i18n";
import type { LatestReports, ReportBundle, ReportKind, ReportRecord } from "../types";

function localeQuery(locale: Locale) {
  return `locale=${encodeURIComponent(locale)}`;
}

export function sendReport(
  projectId: number,
  locale: Locale,
): Promise<{ ok: boolean; recipient?: string; report_id?: number; locale?: string; error?: string }> {
  return apiJson(`/projects/${projectId}/report?${localeQuery(locale)}`, {
    method: "POST",
    body: JSON.stringify({ locale }),
  });
}

export function listReports(projectId: number, locale: Locale): Promise<ReportRecord[]> {
  return apiJson<ReportRecord[]>(`/projects/${projectId}/reports?${localeQuery(locale)}`);
}

export function getLatestReports(projectId: number, locale: Locale): Promise<LatestReports> {
  return apiJson<LatestReports>(`/projects/${projectId}/reports/latest?${localeQuery(locale)}`);
}

export function regenerateReport(projectId: number, kind: ReportKind, locale: Locale): Promise<ReportBundle> {
  return apiJson<ReportBundle>(`/projects/${projectId}/reports/${kind}/regenerate?${localeQuery(locale)}`, {
    method: "POST",
    body: JSON.stringify({ locale }),
  });
}
