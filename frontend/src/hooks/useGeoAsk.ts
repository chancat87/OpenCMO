import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { askGeo, getGeoPlatforms } from "../api/geo";
import type { GeoAskResponse, GeoPlatformsResponse } from "../api/geo";

export function useGeoPlatforms(projectId: number) {
  return useQuery<GeoPlatformsResponse>({
    queryKey: ["geo-platforms", projectId],
    queryFn: () => getGeoPlatforms(projectId),
    staleTime: 60_000,
    enabled: Number.isFinite(projectId) && projectId > 0,
  });
}

export function useGeoAsk(projectId: number) {
  const [lastResult, setLastResult] = useState<GeoAskResponse | null>(null);
  const mutation = useMutation<
    GeoAskResponse,
    Error,
    { query: string; platforms?: string[] | null }
  >({
    mutationFn: (body) => askGeo(projectId, body),
    onSuccess: (data) => {
      setLastResult(data);
    },
  });

  const reset = () => {
    setLastResult(null);
    mutation.reset();
  };

  return {
    ask: mutation.mutate,
    askAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
    result: lastResult,
    reset,
  };
}
