import { useDocuments } from "@/hooks/useDocuments";
import { useActiveProject } from "@/contexts/ProjectContext";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentCard } from "@/components/documents/DocumentCard";

export function DocumentsPage() {
  const { activeProject } = useActiveProject();
  const { data: documents, isLoading } = useDocuments(activeProject?.id || "");

  if (!activeProject) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Documents</h1>
        <p className="text-muted-foreground">
          Select a project to view and manage documents.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Documents</h1>
      <UploadDropzone projectId={activeProject.id} />
      {isLoading ? (
        <p className="text-muted-foreground">Loading documents...</p>
      ) : documents?.length === 0 ? (
        <p className="text-muted-foreground">No documents uploaded yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {documents?.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} projectId={activeProject.id} />
          ))}
        </div>
      )}
    </div>
  );
}
