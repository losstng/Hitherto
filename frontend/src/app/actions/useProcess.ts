// src/hooks/useProcess.ts
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiResponse } from "@/lib/types";

const wrap = <T,>(url: string) =>
  useMutation(async () => {
    const { data } = await api.post<ApiResponse<T>>(url);
    if (!data.success) throw new Error(data.error);
    return data.data!;
  });

export const useExtract  = (id: string) => wrap(`/ingest/extract_text/${id}`);
export const useChunk    = (id: string) => wrap(`/ingest/chunk/${id}`);
export const useEmbed    = (id: string) => wrap(`/ingest/embed/${id}`);
export const useTokenize = (id: string) => wrap(`/ingest/tokenize/${id}`);
