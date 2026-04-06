import { useState } from "react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import type { Contradiction } from "../../lib/api";

interface ContradictionCardProps {
  contradiction: Contradiction;
  onResolve: (id: string, note?: string) => void;
  onDismiss: (id: string, note?: string) => void;
  onReopen: (id: string) => void;
}

export function ContradictionCard({ contradiction, onResolve, onDismiss, onReopen }: ContradictionCardProps) {
  const [note, setNote] = useState("");

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
          <div className="space-y-3">
            <textarea
              className="w-full rounded border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
              placeholder="Resolution note (optional)"
              rows={2}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onResolve(contradiction.id, note || undefined)}>
                Resolve
              </Button>
              <Button size="sm" variant="outline" onClick={() => onDismiss(contradiction.id, note || undefined)}>
                Dismiss
              </Button>
            </div>
          </div>
        )}
        {contradiction.status !== "open" && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              {contradiction.status === "resolved" ? "Resolved" : "Dismissed"}
              {contradiction.resolved_at && ` on ${new Date(contradiction.resolved_at).toLocaleDateString()}`}
            </p>
            {contradiction.resolution_note && (
              <p className="text-sm bg-muted rounded p-3">
                <span className="font-medium">Note:</span> {contradiction.resolution_note}
              </p>
            )}
            <Button size="sm" variant="ghost" onClick={() => onReopen(contradiction.id)}>
              Reopen
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
