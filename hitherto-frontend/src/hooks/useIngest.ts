// src/hooks/useIngest.ts
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiResponse, NewsletterLite, ReloadResp } from "@/lib/types";

export const useReload = () =>
  useMutation(async () => {
    const { data } = await api.post<ApiResponse<ReloadResp>>("/ingest/bloomberg_reload");
    if (!data.success) throw new Error(data.error);
    return data.data!;
  });

export const useCategory = (category: string) =>
  useQuery({
    queryKey: ["news", category],
    enabled: Boolean(category),
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<NewsletterLite[]>>(
        "/ingest/category_filter",
        { params: { category } }
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });
