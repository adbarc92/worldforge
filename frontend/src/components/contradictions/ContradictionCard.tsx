import { useState } from "react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import type { Contradiction } from "../../lib/api";

type Selection = "a" | "b" | "both" | null;

interface ContradictionCardProps {
  contradiction: Contradiction;
  onResolve: (id: string, note?: string) => void;
  onDismiss: (id: string, note?: string) => void;
  onReopen: (id: string) => void;
}

export function ContradictionCard({ contradiction, onResolve, onDismiss, onReopen }: ContradictionCardProps) {
  const [selection, setSelection] = useState<Selection>(null);
  const [note, setNote] = useState("");

  const labelA = contradiction.document_a_title || "Passage A";
  const labelB = contradiction.document_b_title || "Passage B";

  const handleResolve = () => {
    let resolveNote: string | undefined;
    if (selection === "a") {
      resolveNote = `"${labelA}" is canon`;
    } else if (selection === "b") {
      resolveNote = `"${labelB}" is canon`;
    } else if (selection === "both") {
      resolveNote = note || "Both passages are canon";
    }
    onResolve(contradiction.id, resolveNote);
  };

  const toggleSelection = (side: "a" | "b") => {
    setSelection((prev) => {
      if (prev === side) return null;
      if (prev === "both") return side === "a" ? "b" : "a";
      if (prev === null) return side;
      // prev is the other side, selecting this makes it "both"
      return "both";
    });
  };

  const selectedClass = "ring-2 ring-primary bg-primary/10";

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <button
            type="button"
            className={`relative text-left rounded p-3 bg-muted transition-all ${
              contradiction.status === "open" ? "cursor-pointer hover:ring-1 hover:ring-primary/50" : ""
            } ${selection === "a" || selection === "both" ? selectedClass : ""}`}
            onClick={() => contradiction.status === "open" && toggleSelection("a")}
            disabled={contradiction.status !== "open"}
          >
            {(selection === "a" || selection === "both") && (
              <span className="absolute top-1.5 right-2 text-[10px] font-semibold uppercase tracking-wide text-primary">
                Canon
              </span>
            )}
            <p className="text-xs font-medium text-muted-foreground mb-1">{labelA}</p>
            <p className="text-sm">{contradiction.chunk_a_text}</p>
          </button>
          <button
            type="button"
            className={`relative text-left rounded p-3 bg-muted transition-all ${
              contradiction.status === "open" ? "cursor-pointer hover:ring-1 hover:ring-primary/50" : ""
            } ${selection === "b" || selection === "both" ? selectedClass : ""}`}
            onClick={() => contradiction.status === "open" && toggleSelection("b")}
            disabled={contradiction.status !== "open"}
          >
            {(selection === "b" || selection === "both") && (
              <span className="absolute top-1.5 right-2 text-[10px] font-semibold uppercase tracking-wide text-primary">
                Canon
              </span>
            )}
            <p className="text-xs font-medium text-muted-foreground mb-1">{labelB}</p>
            <p className="text-sm">{contradiction.chunk_b_text}</p>
          </button>
        </div>
        <p className="text-sm mb-4">
          <span className="font-medium">Explanation:</span> {contradiction.explanation}
        </p>
        {contradiction.status === "open" && (
          <div className="space-y-3">
            {!selection && (
              <p className="text-xs text-muted-foreground">
                Select the canonical passage, or select both to explain how they coexist.
              </p>
            )}
            {selection === "a" && (
              <p className="text-sm text-muted-foreground">
                Resolving with <span className="font-medium">{labelA}</span> as canon.
              </p>
            )}
            {selection === "b" && (
              <p className="text-sm text-muted-foreground">
                Resolving with <span className="font-medium">{labelB}</span> as canon.
              </p>
            )}
            {selection === "both" && (
              <textarea
                className="w-full rounded border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                placeholder="Explain how both passages are canon..."
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            )}
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={!selection || (selection === "both" && !note.trim())}
                onClick={handleResolve}
              >
                Resolve
              </Button>
              <Button size="sm" variant="outline" onClick={() => onDismiss(contradiction.id)}>
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
