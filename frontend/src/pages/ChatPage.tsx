import { useChat } from "@/hooks/useChat";
import { ChatView } from "@/components/chat/ChatView";

export function ChatPage() {
  const { messages, isLoading, send, clear } = useChat();

  return (
    <ChatView
      messages={messages}
      isLoading={isLoading}
      onSend={send}
      onClear={clear}
    />
  );
}
