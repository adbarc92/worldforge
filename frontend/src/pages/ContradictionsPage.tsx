import { useState } from "react";
import { Button } from "../components/ui/button";
import { ContradictionCard } from "../components/contradictions/ContradictionCard";
import {
  useContradictions,
  useScanContradictions,
  useResolveContradiction,
  useDismissContradiction,
  useReopenContradiction,
} from "../hooks/useContradictions";
import { useActiveProject } from "../contexts/ProjectContext";
import { toast } from "sonner";

const TABS = ["open", "resolved", "dismissed"] as const;

export function ContradictionsPage() {
  const [activeTab, setActiveTab] = useState<string>("open");
  const { activeProject } = useActiveProject();
  const { data, isLoading } = useContradictions(activeTab);
  const scan = useScanContradictions();
  const resolve = useResolveContradiction();
  const dismiss = useDismissContradiction();
  const reopen = useReopenContradiction();

  const handleScan = () => {
    scan.mutate(undefined, {
      onSuccess: () => toast.info("Scanning for contradictions... Refresh in a moment to see results."),
      onError: () => toast.error("Failed to start scan"),
    });
  };

  if (!activeProject) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Contradictions</h1>
        <p className="text-muted-foreground">
          Select a project to view and scan for contradictions.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Contradictions</h1>
          {data && <p className="text-sm text-muted-foreground">{data.total} {activeTab}</p>}
        </div>
        <Button onClick={handleScan} disabled={scan.isPending}>
          {scan.isPending ? "Starting scan..." : "Scan Project"}
        </Button>
      </div>

      <div className="flex gap-1 mb-6">
        {TABS.map((tab) => (
          <Button
            key={tab}
            variant={activeTab === tab ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Button>
        ))}
      </div>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No {activeTab} contradictions.</p>
      )}

      <div className="space-y-4">
        {data?.items.map((c) => (
          <ContradictionCard
            key={c.id}
            contradiction={c}
            onResolve={(id, note) => resolve.mutate({ id, note })}
            onDismiss={(id, note) => dismiss.mutate({ id, note })}
            onReopen={(id) => reopen.mutate(id)}
          />
        ))}
      </div>
    </div>
  );
}

export default ContradictionsPage;
