import { apiJson } from "./client";

export interface GitHubStats {
  stars: number | null;
  contributors: number | null;
  last_commit_iso: string | null;
  fetched_at: string | null;
}

export function getGitHubStats(): Promise<GitHubStats> {
  return apiJson<GitHubStats>("/github-stats");
}
