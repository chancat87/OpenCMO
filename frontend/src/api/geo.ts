import { apiJson } from "./client";
import type { GeoScan, ChartData } from "../types";

export type GeoAskSourceStatus = "ok" | "empty" | "blocked" | "error";

export interface GeoAskPlatformResult {
  platform: string;
  mentioned: boolean;
  mention_count: number;
  position_pct: number | null;
  content_snippet: string;
  source_status: GeoAskSourceStatus;
  error: string | null;
  duration_ms: number;
}

export interface GeoAskResponse {
  query: string;
  results: GeoAskPlatformResult[];
  total_duration_ms: number;
  query_lang: "en" | "zh";
}

export interface GeoPlatformInfo {
  name: string;
  enabled: boolean;
  requires_auth: boolean;
  auth_env_vars: string[];
}

export interface GeoPlatformsResponse {
  platforms: GeoPlatformInfo[];
}

export function getGeoHistory(projectId: number): Promise<GeoScan[]> {
  return apiJson<GeoScan[]>(`/projects/${projectId}/geo/history`);
}

export function getGeoChart(projectId: number): Promise<ChartData> {
  return apiJson<ChartData>(`/projects/${projectId}/geo/chart`);
}

export function askGeo(
  projectId: number,
  body: { query: string; platforms?: string[] | null },
): Promise<GeoAskResponse> {
  return apiJson<GeoAskResponse>(`/projects/${projectId}/geo/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function getGeoPlatforms(projectId: number): Promise<GeoPlatformsResponse> {
  return apiJson<GeoPlatformsResponse>(`/projects/${projectId}/geo/platforms`);
}
