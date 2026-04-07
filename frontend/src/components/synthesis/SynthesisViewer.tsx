import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "../ui/button";
import { useActiveProject } from "../../contexts/ProjectContext";
import { api } from "../../lib/api";

interface SynthesisViewerProps {
  synthesisId: string;
  title: string;
  content: string;
  onRegenerate: () => void;
}

export function SynthesisViewer({ synthesisId, title, content, onRegenerate }: SynthesisViewerProps) {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;

  const handleDownload = () => {
    if (!projectId) return;
    window.open(api.synthesis.download(projectId, synthesisId), "_blank");
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownload}>
            Download
          </Button>
          <Button variant="outline" onClick={onRegenerate}>
            Regenerate
          </Button>
        </div>
      </div>
      <div className="rounded border border-input p-6 prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
