import { useState } from "react";
import { Button } from "../components/ui/button";
import { OutlineEditor } from "../components/synthesis/OutlineEditor";
import { SynthesisViewer } from "../components/synthesis/SynthesisViewer";
import {
  useSyntheses,
  useSynthesis,
  useCreateSynthesis,
  useUpdateOutline,
  useApproveSynthesis,
  useRetrySynthesis,
} from "../hooks/useSynthesis";
import { useContradictions } from "../hooks/useContradictions";
import { useActiveProject } from "../contexts/ProjectContext";
import { toast } from "sonner";

export function SynthesisPage() {
  const { activeProject } = useActiveProject();
  const [activeSynthesisId, setActiveSynthesisId] = useState<string | null>(null);
  const [prevProjectId, setPrevProjectId] = useState<string | undefined>(activeProject?.id);

  const { data: syntheses } = useSyntheses();
  const { data: synthesis } = useSynthesis(activeSynthesisId);
  const { data: contradictions } = useContradictions("open");
  const createSynthesis = useCreateSynthesis();
  const updateOutline = useUpdateOutline();
  const approveSynthesis = useApproveSynthesis();
  const retrySynthesis = useRetrySynthesis();

  const openCount = contradictions?.total ?? 0;
  const gateBlocked = openCount > 0;

  // Reset when project changes (state-based comparison during render)
  if (activeProject?.id !== prevProjectId) {
    setPrevProjectId(activeProject?.id);
    setActiveSynthesisId(null);
  }

  // Auto-select the most recent synthesis
  if (syntheses && syntheses.length > 0 && !activeSynthesisId && activeProject?.id === prevProjectId) {
    setActiveSynthesisId(syntheses[0].id);
  }

  if (!activeProject) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Synthesis</h1>
        <p className="text-muted-foreground">
          Select a project to generate a world primer.
        </p>
      </div>
    );
  }

  const handleCreate = (auto: boolean) => {
    createSynthesis.mutate(auto, {
      onSuccess: (data) => {
        setActiveSynthesisId(data.id);
        toast.success(auto ? "Quick generation started..." : "Outline generation started...");
      },
      onError: () => toast.error("Failed to create synthesis"),
    });
  };

  const handleSaveOutline = (outline: import("../lib/api").SynthesisOutlineSection[]) => {
    if (!activeSynthesisId) return;
    updateOutline.mutate(
      { id: activeSynthesisId, outline },
      {
        onSuccess: () => toast.success("Outline saved"),
        onError: () => toast.error("Failed to save outline"),
      }
    );
  };

  const handleApprove = () => {
    if (!activeSynthesisId) return;
    approveSynthesis.mutate(activeSynthesisId, {
      onSuccess: () => toast.success("Generating sections..."),
      onError: () => toast.error("Failed to approve outline"),
    });
  };

  const handleRegenerate = () => {
    handleCreate(false);
  };

  // Determine page content based on state
  const renderContent = () => {
    // No active synthesis yet
    if (!synthesis && !activeSynthesisId) {
      if (gateBlocked) {
        return (
          <div className="space-y-4">
            <p className="text-sm text-red-500">
              There are {openCount} open contradiction(s). Resolve or dismiss them before generating a synthesis.
            </p>
            <div className="flex gap-2">
              <Button disabled>Generate World Primer</Button>
              <Button variant="outline" disabled>Quick Generate</Button>
            </div>
          </div>
        );
      }

      return (
        <div className="flex gap-2">
          <Button onClick={() => handleCreate(false)} disabled={createSynthesis.isPending}>
            {createSynthesis.isPending ? "Starting..." : "Generate World Primer"}
          </Button>
          <Button variant="outline" onClick={() => handleCreate(true)} disabled={createSynthesis.isPending}>
            Quick Generate
          </Button>
        </div>
      );
    }

    if (!synthesis) {
      return <p className="text-muted-foreground">Loading...</p>;
    }

    switch (synthesis.status) {
      case "outline_pending":
        return <p className="text-muted-foreground">Generating outline...</p>;

      case "outline_ready":
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Edit Outline</h2>
            <OutlineEditor
              outline={synthesis.outline ?? []}
              onSave={handleSaveOutline}
              onApprove={handleApprove}
            />
          </div>
        );

      case "generating":
        return (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
              <p className="text-muted-foreground">Generating sections...</p>
            </div>
            <OutlineEditor
              outline={synthesis.outline ?? []}
              readOnly
              onSave={() => {}}
              onApprove={() => {}}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => retrySynthesis.mutate(synthesis.id, {
                onSuccess: () => toast.info("Reset to outline review — you can re-approve to retry."),
              })}
            >
              Stuck? Reset to outline
            </Button>
          </div>
        );

      case "completed":
        return (
          <SynthesisViewer
            synthesisId={synthesis.id}
            title={synthesis.title}
            content={synthesis.content ?? ""}
            onRegenerate={handleRegenerate}
          />
        );

      case "failed":
        return (
          <div className="space-y-4">
            <p className="text-sm text-red-500">
              Synthesis failed: {synthesis.error_message || "Unknown error"}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => retrySynthesis.mutate(synthesis.id, {
                  onSuccess: () => toast.info("Reset to outline review — edit or re-approve to retry."),
                })}
              >
                Retry with same outline
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleCreate(false)}>
                Start fresh
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const otherSyntheses = syntheses?.filter((s) => s.id !== activeSynthesisId) ?? [];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Synthesis</h1>
        <p className="text-sm text-muted-foreground">
          Generate a comprehensive world primer from your canon.
        </p>
      </div>

      {renderContent()}

      {otherSyntheses.length > 0 && (
        <div className="mt-10">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">Previous Syntheses</h3>
          <div className="space-y-2">
            {otherSyntheses.map((s) => (
              <button
                key={s.id}
                className="w-full text-left rounded border border-input bg-muted/40 px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                onClick={() => setActiveSynthesisId(s.id)}
              >
                <span className="font-medium">{s.title}</span>
                <span className="ml-2 text-muted-foreground">
                  ({s.status}) &mdash; {new Date(s.created_at).toLocaleDateString()}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SynthesisPage;
