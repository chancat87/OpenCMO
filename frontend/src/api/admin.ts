import { apiJson } from "./client";
import type { AdminSummary } from "../types";

export function getAdminSummary(): Promise<AdminSummary> {
  return apiJson<AdminSummary>("/admin/summary");
}

export function disableAccount(accountId: number): Promise<{ ok: boolean }> {
  return apiJson(`/admin/accounts/${accountId}/disable`, { method: "POST" });
}

export function enableAccount(accountId: number): Promise<{ ok: boolean }> {
  return apiJson(`/admin/accounts/${accountId}/enable`, { method: "POST" });
}

export function extendTrial(accountId: number, days: number): Promise<{ ok: boolean }> {
  return apiJson(`/admin/accounts/${accountId}/extend-trial`, {
    method: "POST",
    body: JSON.stringify({ days }),
  });
}

export function updateQuota(
  accountId: number,
  payload: { max_projects?: number; daily_scan_limit?: number; monthly_report_limit?: number },
): Promise<{ ok: boolean }> {
  return apiJson(`/admin/accounts/${accountId}/quota`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
