import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDeleteDocument } from "@/hooks/useDocuments";
import { toast } from "sonner";
import type { Document } from "@/lib/api";

export function DocumentCard({ doc }: { doc: Document }) {
  const deleteMutation = useDeleteDocument();

  const statusColor =
    doc.status === "processed"
      ? "bg-green-100 text-green-800"
      : doc.status === "error"
        ? "bg-red-100 text-red-800"
        : "bg-yellow-100 text-yellow-800";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{doc.title}</CardTitle>
            <CardDescription>
              {doc.created_at
                ? new Date(doc.created_at).toLocaleDateString()
                : ""}
            </CardDescription>
          </div>
          <Badge variant="outline" className={statusColor}>
            {doc.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {doc.chunk_count} chunks
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => {
              if (confirm(`Delete "${doc.title}"?`)) {
                deleteMutation.mutate(doc.id, {
                  onSuccess: () => toast.success("Document deleted"),
                  onError: (err) => toast.error(err.message),
                });
              }
            }}
          >
            Delete
          </Button>
        </div>
        {doc.error_message && (
          <p className="text-sm text-destructive mt-2">{doc.error_message}</p>
        )}
      </CardContent>
    </Card>
  );
}
