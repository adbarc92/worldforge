import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { useActiveProject } from "@/contexts/ProjectContext";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: { title: string; relevance_score: number }[];
}

export function useChat(projectId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { setActiveProject } = useActiveProject();
  const queryClient = useQueryClient();

  const send = useCallback(
    async (question: string) => {
      const userMsg: ChatMessage = { role: "user", content: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const result = await api.query(projectId, question);
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: result.answer,
          citations: result.citations,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        // If the project was deleted out from under us, self-heal: clear the
        // stale activeProject and force the projects list to refetch so the
        // ChatPage falls back to "Select a project" on next render.
        if (err instanceof ApiError && err.status === 404) {
          setActiveProject(null);
          queryClient.invalidateQueries({ queryKey: ["projects"] });
        }
        const errorMsg: ChatMessage = {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [projectId, setActiveProject, queryClient]
  );

  const clear = useCallback(() => setMessages([]), []);

  return { messages, isLoading, send, clear };
}
