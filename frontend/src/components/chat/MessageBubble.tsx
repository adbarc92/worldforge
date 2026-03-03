import { Badge } from "@/components/ui/badge";
import type { ChatMessage } from "@/hooks/useChat";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.citations.map((c, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {c.title} ({Math.round(c.relevance_score * 100)}%)
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
