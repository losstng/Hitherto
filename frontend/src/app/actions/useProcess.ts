// src/hooks/useProcess.ts
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiResponse } from "@/lib/types";

const useWrap = <T,>(url: string) =>
  useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<T>>(url);
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });

export const useExtract  = (id: string) => useWrap(`/ingest/extract_text/${id}`);
export const useChunk    = (id: string) => useWrap(`/ingest/chunk/${id}`);
export const useEmbed    = (id: string) => useWrap(`/ingest/embed/${id}`);
export const useTokenize = (id: string) => useWrap(`/ingest/tokenize/${id}`);
