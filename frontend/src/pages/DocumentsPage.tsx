import { useDocuments } from "@/hooks/useDocuments";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentCard } from "@/components/documents/DocumentCard";

export function DocumentsPage() {
  const { data: documents, isLoading } = useDocuments();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Documents</h1>
      <UploadDropzone />
      {isLoading ? (
        <p className="text-muted-foreground">Loading documents...</p>
      ) : documents?.length === 0 ? (
        <p className="text-muted-foreground">No documents uploaded yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {documents?.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
