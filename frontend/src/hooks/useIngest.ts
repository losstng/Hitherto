import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiResponse, NewsletterLite } from "@/lib/types";

export const useReload = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<NewsletterLite[]>>(
        "/ingest/bloomberg_reload"
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["category"] });
    },
  });
};

export const useCategory = (category: string) =>
  useQuery({
    queryKey: ["category", category],
    queryFn: async () => {
      if (!category) {
        const { data } = await api.post<ApiResponse<NewsletterLite[]>>(
          "/ingest/bloomberg_reload"
        );
        if (!data.success) throw new Error(data.error);
        return data.data!;
      }
      const { data } = await api.get<ApiResponse<NewsletterLite[]>>(
        "/ingest/category_filter",
        { params: { category } }
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });
