import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import type { Contradiction } from "../../lib/api";

interface ContradictionCardProps {
  contradiction: Contradiction;
  onResolve: (id: string) => void;
  onDismiss: (id: string) => void;
}

export function ContradictionCard({ contradiction, onResolve, onDismiss }: ContradictionCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              {contradiction.document_a_title || "Passage A"}
            </p>
            <p className="text-sm bg-muted rounded p-3">{contradiction.chunk_a_text}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              {contradiction.document_b_title || "Passage B"}
            </p>
            <p className="text-sm bg-muted rounded p-3">{contradiction.chunk_b_text}</p>
          </div>
        </div>
        <p className="text-sm mb-4">
          <span className="font-medium">Explanation:</span> {contradiction.explanation}
        </p>
        {contradiction.status === "open" && (
          <div className="flex gap-2">
            <Button size="sm" onClick={() => onResolve(contradiction.id)}>
              Resolve
            </Button>
            <Button size="sm" variant="outline" onClick={() => onDismiss(contradiction.id)}>
              Dismiss
            </Button>
          </div>
        )}
        {contradiction.status !== "open" && (
          <p className="text-xs text-muted-foreground">
            {contradiction.status === "resolved" ? "Resolved" : "Dismissed"}
            {contradiction.resolved_at && ` on ${new Date(contradiction.resolved_at).toLocaleDateString()}`}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
