import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useActiveProject } from "@/contexts/ProjectContext";

export function useContradictions(status: string = "open") {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  return useQuery({
    queryKey: ["contradictions", projectId, status],
    queryFn: () => api.contradictions.list(projectId!, status),
    enabled: !!projectId,
  });
}

export function useScanContradictions() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.contradictions.scan(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}

export function useResolveContradiction() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.contradictions.resolve(projectId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}

export function useDismissContradiction() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.contradictions.dismiss(projectId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contradictions", projectId] });
    },
  });
}
