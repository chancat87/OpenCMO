import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getLatestReports, listReports, regenerateReport, sendReport } from "../api/report";
import type { Locale } from "../i18n";
import type { ReportKind } from "../types";

export function useLatestReports(projectId: number, locale: Locale) {
  return useQuery({
    queryKey: ["latest-reports", projectId, locale],
    queryFn: () => getLatestReports(projectId, locale),
  });
}

export function useReports(projectId: number, locale: Locale) {
  return useQuery({
    queryKey: ["reports", projectId, locale],
    queryFn: () => listReports(projectId, locale),
  });
}

export function useRegenerateReport(projectId: number, locale: Locale) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kind: ReportKind) => regenerateReport(projectId, kind, locale),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["reports", projectId, locale] }),
        qc.invalidateQueries({ queryKey: ["latest-reports", projectId, locale] }),
        qc.invalidateQueries({ queryKey: ["project-summary", projectId] }),
      ]);
    },
  });
}

export function useSendReport(projectId: number, locale: Locale) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => sendReport(projectId, locale),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["reports", projectId, locale] }),
        qc.invalidateQueries({ queryKey: ["latest-reports", projectId, locale] }),
      ]);
    },
  });
}
