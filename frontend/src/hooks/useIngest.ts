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
      client.invalidateQueries({ queryKey: ["filter"] });
    },
  });
};

export const useFilters = (category: string, date: string) =>
  useQuery({
    queryKey: ["filter", category, date],
    queryFn: async () => {
      if (!category && !date) {
        const { data } = await api.post<ApiResponse<NewsletterLite[]>>(
          "/ingest/bloomberg_reload"
        );
        if (!data.success) throw new Error(data.error);
        return data.data!;
      }
      const { data } = await api.get<ApiResponse<NewsletterLite[]>>(
        "/ingest/filter",
        { params: { category: category || undefined, date: date || undefined } }
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });

export const useCategories = () =>
  useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<string[]>>("/ingest/categories");
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });
