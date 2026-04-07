import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useActiveProject } from "@/contexts/ProjectContext";
import type { SynthesisOutlineSection } from "@/lib/api";

export function useSyntheses() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  return useQuery({
    queryKey: ["syntheses", projectId],
    queryFn: () => api.synthesis.list(projectId!),
    enabled: !!projectId,
  });
}

export function useSynthesis(id: string | null) {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  return useQuery({
    queryKey: ["synthesis", projectId, id],
    queryFn: () => api.synthesis.get(projectId!, id!),
    enabled: !!projectId && !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "outline_pending" || status === "generating") {
        return 5000;
      }
      return false;
    },
  });
}

export function useCreateSynthesis() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (auto: boolean = false) => api.synthesis.create(projectId!, auto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["syntheses", projectId] });
    },
  });
}

export function useUpdateOutline() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, outline }: { id: string; outline: SynthesisOutlineSection[] }) =>
      api.synthesis.updateOutline(projectId!, id, outline),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["synthesis", projectId, vars.id] });
    },
  });
}

export function useApproveSynthesis() {
  const { activeProject } = useActiveProject();
  const projectId = activeProject?.id;
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.synthesis.approve(projectId!, id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["synthesis", projectId, id] });
    },
  });
}
