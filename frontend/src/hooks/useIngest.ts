import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiResponse, NewsletterLite } from "@/lib/types";

export const useReload = () =>
  useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<NewsletterLite[]>>(
        "/ingest/bloomberg_reload"
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });

export const useCategory = (category: string) =>
  useQuery({
    queryKey: ["category", category],
    enabled: !!category,
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<NewsletterLite[]>>(
        "/ingest/category_filter",
        { params: { category } }
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });
