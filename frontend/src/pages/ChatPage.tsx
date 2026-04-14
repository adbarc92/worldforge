import { useChat } from "@/hooks/useChat";
import { useActiveProject } from "@/contexts/ProjectContext";
import { ChatView } from "@/components/chat/ChatView";

export function ChatPage() {
  const { activeProject } = useActiveProject();
  const { messages, isLoading, send, clear } = useChat(activeProject?.id || "");

  if (!activeProject) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">
          Select a project to start chatting.
        </p>
      </div>
    );
  }

  return (
    <ChatView
      messages={messages}
      isLoading={isLoading}
      onSend={send}
      onClear={clear}
    />
  );
}
