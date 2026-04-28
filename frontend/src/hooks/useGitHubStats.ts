import { useQuery } from "@tanstack/react-query";
import { getGitHubStats, type GitHubStats } from "../api/githubStats";

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

export function useGitHubStats() {
  return useQuery<GitHubStats>({
    queryKey: ["github-stats"],
    queryFn: getGitHubStats,
    staleTime: ONE_DAY_MS,
    gcTime: ONE_DAY_MS,
    retry: 1,
  });
}
