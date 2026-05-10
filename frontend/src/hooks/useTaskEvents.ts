import { useEffect, useRef, useState, useCallback } from "react";

export interface TaskEvent {
  type: "progress" | "done" | "error";
  stage?: string;
  status?: string;
  agent?: string;
  summary?: string;
  detail?: string;
  /* done-specific fields */
  run_id?: number;
  findings_count?: number;
  recommendations_count?: number;
  error?: string | null;
  message?: string;
}

interface UseTaskEventsOptions {
  /** Called when the task finishes (status == done). */
  onDone?: (event: TaskEvent) => void;
  /** Enable/disable the connection. Defaults to true. */
  enabled?: boolean;
}

/**
 * Subscribe to real-time task progress via Server-Sent Events.
 *
 * Returns an array of received events and a boolean indicating whether
 * the connection is still active.
 */
export function useTaskEvents(
  taskId: string | null | undefined,
  options: UseTaskEventsOptions = {},
) {
  const { onDone, enabled = true } = options;
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  const reset = useCallback(() => {
    setEvents([]);
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    if (!taskId || !enabled) {
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setIsStreaming(true);
    setEvents([]);

    const handleMessage = (data: string) => {
      try {
        const event: TaskEvent = JSON.parse(data);
        setEvents((prev) => [...prev, event]);

        if (event.type === "done" || event.type === "error") {
          setIsStreaming(false);
          controller.abort();
          onDoneRef.current?.(event);
        }
      } catch {
        // Ignore malformed events
      }
    };

    const readStream = async () => {
      const headers = new Headers();
      const token = localStorage.getItem("opencmo_token");
      if (token) headers.set("Authorization", `Bearer ${token}`);

      try {
        const resp = await fetch(`/api/v1/tasks/${taskId}/events`, {
          headers,
          signal: controller.signal,
        });

        if (resp.status === 401) {
          window.dispatchEvent(new CustomEvent("opencmo:unauthorized"));
        }
        if (!resp.ok || !resp.body) {
          setIsStreaming(false);
          return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!cancelled) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split("\n\n");
          buffer = chunks.pop() ?? "";

          for (const chunk of chunks) {
            const data = chunk
              .split("\n")
              .filter((line) => line.startsWith("data:"))
              .map((line) => line.slice(5).trimStart())
              .join("\n");
            if (data) handleMessage(data);
          }
        }
      } catch {
        if (!controller.signal.aborted) {
          setIsStreaming(false);
        }
        return;
      }

      if (!cancelled) setIsStreaming(false);
    };

    void readStream();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [taskId, enabled]);

  return { events, isStreaming, reset };
}
