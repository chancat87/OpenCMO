import { useState, useCallback, useEffect } from "react";
import {
  createSession,
  streamChat,
  listSessions,
  getSessionMessages,
  deleteSession,
} from "../api/chat";
import type { ChatMessage, ChatEvent, ToolStatus, ChatSessionSummary } from "../types";

let msgIdCounter = 0;
function nextId() {
  return `msg-${++msgIdCounter}`;
}

export function useChat(initialProjectId: number | null = null) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<number | null>(initialProjectId);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("CMO Agent");

  const refreshSessions = useCallback(async () => {
    try {
      const list = await listSessions();
      setSessions(list);
    } catch {
      // ignore
    }
  }, []);

  // Load sessions + create initial session on mount
  useEffect(() => {
    let cancelled = false;

    void refreshSessions();
    createSession(initialProjectId)
      .then(async (id) => {
        if (cancelled) return;
        setSessionId(id);
        setProjectId(initialProjectId);
        await refreshSessions();
      })
      .catch(console.error);

    return () => {
      cancelled = true;
    };
  }, [initialProjectId, refreshSessions]);

  const loadSession = useCallback(
    async (id: string) => {
      if (isStreaming) return;
      try {
        const msgs = await getSessionMessages(id);
        const session = sessions.find((item) => item.id === id);
        setSessionId(id);
        setProjectId(session?.project_id ?? null);
        setMessages(
          msgs.map((m) => ({
            id: nextId(),
            role: m.role as "user" | "assistant",
            content: m.content,
          })),
        );
        setCurrentAgent("CMO Agent");
      } catch {
        // session might be stale
      }
    },
    [isStreaming, sessions],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!sessionId || isStreaming || !content.trim()) return;

      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content: content.trim(),
      };
      const assistantMsg: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content: "",
        agent: currentAgent,
        tools: [],
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      try {
        for await (const event of streamChat(sessionId, content.trim(), projectId)) {
          handleEvent(event, assistantMsg.id);
        }
        // Refresh session list after completion (title may have changed)
        await refreshSessions();
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? {
                  ...m,
                  content:
                    m.content ||
                    `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
                }
              : m,
          ),
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId, isStreaming, currentAgent, projectId, refreshSessions],
  );

  const handleEvent = useCallback(
    (event: ChatEvent, msgId: string) => {
      switch (event.type) {
        case "delta":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, content: m.content + (event.content ?? "") }
                : m,
            ),
          );
          break;
        case "agent":
          setCurrentAgent(event.name ?? "CMO Agent");
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId ? { ...m, agent: event.name } : m,
            ),
          );
          break;
        case "tool_call":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    tools: [
                      ...(m.tools ?? []),
                      { name: event.name ?? "tool", done: false },
                    ],
                  }
                : m,
            ),
          );
          break;
        case "tool_done":
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msgId) return m;
              const tools = [...(m.tools ?? [])];
              const last = tools.findLast((t: ToolStatus) => !t.done);
              if (last) last.done = true;
              return { ...m, tools };
            }),
          );
          break;
        case "handoff":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    tools: [
                      ...(m.tools ?? []),
                      {
                        name: `Handing off to ${event.target}`,
                        done: false,
                      },
                    ],
                  }
                : m,
            ),
          );
          break;
        case "handoff_done":
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msgId) return m;
              const tools = [...(m.tools ?? [])];
              const last = tools.findLast((t: ToolStatus) => !t.done);
              if (last) last.done = true;
              return { ...m, tools };
            }),
          );
          break;
        case "done":
          if (event.agent_name) setCurrentAgent(event.agent_name);
          break;
        case "error":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, content: m.content || `Error: ${event.message}` }
                : m,
            ),
          );
          break;
      }
    },
    [],
  );

  const resetChat = useCallback(async (nextProjectId: number | null = projectId) => {
    if (isStreaming) return;
    setMessages([]);
    setCurrentAgent("CMO Agent");
    setProjectId(nextProjectId);
    try {
      const newId = await createSession(nextProjectId);
      setSessionId(newId);
      await refreshSessions();
    } catch (e) {
      console.error("Failed to create new session", e);
    }
  }, [isStreaming, projectId, refreshSessions]);

  const selectProject = useCallback(
    async (nextProjectId: number | null) => {
      if (nextProjectId === projectId) return;
      await resetChat(nextProjectId);
    },
    [projectId, resetChat],
  );

  const removeSession = useCallback(
    async (id: string) => {
      try {
        await deleteSession(id);
        setSessions((prev) => prev.filter((s) => s.id !== id));
        // If deleted session is the active one, reset
        if (id === sessionId) {
          await resetChat(projectId);
        }
      } catch {
        // ignore
      }
    },
    [projectId, sessionId, resetChat],
  );

  return {
    messages,
    isStreaming,
    currentAgent,
    projectId,
    sendMessage,
    resetChat,
    selectProject,
    sessionReady: !!sessionId,
    sessionId,
    sessions,
    loadSession,
    removeSession,
  };
}
