// src/app/actions/useProcess.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  ApiResponse,
  ExtractResp,
  ChunkResp,
  EmbedResp,
  TokenResp,
} from "@/lib/types";

const useWrap = <T,>(url: string) => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<T>>(url);
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["category"] });
    },
  });
};

export const useExtract = (id: string) =>
  useWrap<ExtractResp>(`/ingest/extract_text/${id}`);
export const useChunk = (id: string) =>
  useWrap<ChunkResp>(`/ingest/chunk/${id}`);
export const useEmbed = (id: string) =>
  useWrap<EmbedResp>(`/ingest/embed/${id}`);
export const useTokenize = (id: string) =>
  useWrap<TokenResp>(`/ingest/tokenize/${id}`);
