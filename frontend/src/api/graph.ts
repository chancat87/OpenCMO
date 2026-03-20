import { apiJson, apiFetch } from "./client";

export interface GraphNode {
  id: string;
  label: string;
  type: "brand" | "keyword" | "discussion" | "serp" | "competitor" | "competitor_keyword";
  url?: string;
  category?: string;
  platform?: string;
  engagement?: number;
  comments?: number;
  position?: number;
  provider?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  type: "has_keyword" | "has_discussion" | "serp_rank" | "competitor_of" | "comp_keyword" | "keyword_overlap";
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface Competitor {
  id: number;
  name: string;
  url: string | null;
  category: string | null;
  created_at: string;
}

export async function fetchGraph(projectId: number): Promise<GraphData> {
  return apiJson<GraphData>(`/projects/${projectId}/graph`);
}

export async function fetchCompetitors(projectId: number): Promise<Competitor[]> {
  return apiJson<Competitor[]>(`/projects/${projectId}/competitors`);
}

export async function addCompetitor(
  projectId: number,
  data: { name: string; url?: string; category?: string; keywords?: string[] },
): Promise<{ id: number; name: string }> {
  return apiJson(`/projects/${projectId}/competitors`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteCompetitor(competitorId: number): Promise<void> {
  await apiFetch(`/competitors/${competitorId}`, { method: "DELETE" });
}
