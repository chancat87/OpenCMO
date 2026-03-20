import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listMonitors, createMonitor, deleteMonitor, runMonitor, updateMonitor } from "../api/monitors";

export function useMonitors() {
  return useQuery({
    queryKey: ["monitors"],
    queryFn: listMonitors,
  });
}

export function useCreateMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createMonitor,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["monitors"] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; cron_expr?: string; enabled?: boolean }) =>
      updateMonitor(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["monitors"] }),
  });
}

export function useDeleteMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteMonitor,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["monitors"] });
    },
  });
}

export function useRunMonitor() {
  return useMutation({ mutationFn: runMonitor });
}
