import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => api.documents.list(projectId),
    enabled: !!projectId,
  });
}

export function useUploadDocument(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.documents.upload(projectId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}

export function useDeleteDocument(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.documents.delete(projectId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}
