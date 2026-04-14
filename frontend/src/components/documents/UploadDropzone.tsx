import { useCallback, useState } from "react";
import { useUploadDocument } from "@/hooks/useDocuments";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";

export function UploadDropzone({ projectId }: { projectId: string }) {
  const upload = useUploadDocument(projectId);
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      Array.from(files).forEach((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (!["txt", "md", "pdf"].includes(ext || "")) {
          toast.error(`Unsupported file type: .${ext}`);
          return;
        }
        upload.mutate(file, {
          onSuccess: (doc) => toast.success(`Uploaded "${doc.title}"`),
          onError: (err) => toast.error(`Upload failed: ${err.message}`),
        });
      });
    },
    [upload]
  );

  return (
    <Card
      className={`border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
        dragging ? "border-primary bg-primary/5" : "border-muted-foreground/25"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".txt,.md,.pdf";
        input.multiple = true;
        input.onchange = () => handleFiles(input.files);
        input.click();
      }}
    >
      <div className="text-muted-foreground">
        <p className="text-lg font-medium">
          {upload.isPending ? "Uploading..." : "Drop files here or click to upload"}
        </p>
        <p className="text-sm mt-1">Supports .txt, .md, .pdf</p>
      </div>
    </Card>
  );
}
