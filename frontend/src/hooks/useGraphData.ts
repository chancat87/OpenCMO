import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGraph, fetchCompetitors, addCompetitor, deleteCompetitor } from "../api/graph";
import type { GraphData, Competitor } from "../api/graph";

export function useGraphData(projectId: number) {
  return useQuery<GraphData>({
    queryKey: ["graph", projectId],
    queryFn: () => fetchGraph(projectId),
    refetchInterval: 30_000, // realtime: refetch every 30s
  });
}

export function useCompetitors(projectId: number) {
  return useQuery<Competitor[]>({
    queryKey: ["competitors", projectId],
    queryFn: () => fetchCompetitors(projectId),
  });
}

export function useAddCompetitor(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; url?: string; category?: string; keywords?: string[] }) =>
      addCompetitor(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useDeleteCompetitor(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (competitorId: number) => deleteCompetitor(competitorId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}
