import { useState } from "react";
import { Button } from "../components/ui/button";
import { ContradictionCard } from "../components/contradictions/ContradictionCard";
import {
  useContradictions,
  useScanContradictions,
  useResolveContradiction,
  useDismissContradiction,
  useReopenContradiction,
  useBulkUpdateContradictions,
} from "../hooks/useContradictions";
import { useActiveProject } from "../contexts/ProjectContext";
import { toast } from "sonner";
import type { Contradiction } from "../lib/api";

const TABS = ["open", "resolved", "dismissed"] as const;

interface DocumentGroup {
  key: string;
  titleA: string;
  titleB: string;
  items: Contradiction[];
}

function groupByDocumentPair(items: Contradiction[]): DocumentGroup[] {
  const groups = new Map<string, DocumentGroup>();
  for (const c of items) {
    const a = c.document_a_title || c.document_a_id || "Unknown";
    const b = c.document_b_title || c.document_b_id || "Unknown";
    // Normalize key so (A,B) and (B,A) end up in the same group
    const sorted = [a, b].sort();
    const key = `${sorted[0]}|||${sorted[1]}`;
    if (!groups.has(key)) {
      groups.set(key, { key, titleA: sorted[0], titleB: sorted[1], items: [] });
    }
    groups.get(key)!.items.push(c);
  }
  return Array.from(groups.values()).sort((a, b) => b.items.length - a.items.length);
}

export function ContradictionsPage() {
  const [activeTab, setActiveTab] = useState<string>("open");
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const { activeProject } = useActiveProject();
  const { data, isLoading } = useContradictions(activeTab);
  const scan = useScanContradictions();
  const resolve = useResolveContradiction();
  const dismiss = useDismissContradiction();
  const reopen = useReopenContradiction();
  const bulk = useBulkUpdateContradictions();

  const handleScan = () => {
    scan.mutate(undefined, {
      onSuccess: () => toast.info("Scanning for contradictions... Refresh in a moment to see results."),
      onError: () => toast.error("Failed to start scan"),
    });
  };

  const toggleGroup = (key: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleBulk = (ids: string[], status: "resolved" | "dismissed", note?: string) => {
    bulk.mutate({ ids, status, note }, {
      onSuccess: (data) => toast.success(`${data.updated} contradictions ${status}`),
      onError: () => toast.error("Bulk update failed"),
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

  const groups = data ? groupByDocumentPair(data.items) : [];

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

      <div className="space-y-6">
        {groups.map((group) => {
          const isCollapsed = collapsedGroups.has(group.key);
          const ids = group.items.map((c) => c.id);
          return (
            <div key={group.key} className="border rounded-lg">
              <div
                className="flex items-center justify-between px-4 py-3 bg-muted/50 rounded-t-lg cursor-pointer"
                onClick={() => toggleGroup(group.key)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {group.titleA} vs {group.titleB}
                  </span>
                  <span className="text-xs text-muted-foreground bg-muted rounded-full px-2 py-0.5">
                    {group.items.length}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {activeTab === "open" && group.items.length > 1 && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => { e.stopPropagation(); handleBulk(ids, "dismissed"); }}
                      >
                        Dismiss Group
                      </Button>
                      <Button
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBulk(ids, "resolved", `"${group.titleA}" and "${group.titleB}" contradictions resolved as a group`);
                        }}
                      >
                        Resolve Group
                      </Button>
                    </>
                  )}
                  <span className="text-muted-foreground text-sm">{isCollapsed ? "▸" : "▾"}</span>
                </div>
              </div>
              {!isCollapsed && (
                <div className="p-4 space-y-4">
                  {group.items.map((c) => (
                    <ContradictionCard
                      key={c.id}
                      contradiction={c}
                      onResolve={(id, note) => resolve.mutate({ id, note })}
                      onDismiss={(id, note) => dismiss.mutate({ id, note })}
                      onReopen={(id) => reopen.mutate(id)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ContradictionsPage;
