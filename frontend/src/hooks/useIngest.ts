import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
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
      client.invalidateQueries({ queryKey: ["newsletters"] });
    },
  });
};

export const useNewsletters = () =>
  useQuery({
    queryKey: ["newsletters"],
    queryFn: async () => {
      const { data } = await api.post<ApiResponse<NewsletterLite[]>>(
        "/ingest/bloomberg_reload"
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });

export const useFilters = (category: string, start: string, end: string) => {
  const { data, isFetching } = useNewsletters();
  const filtered = useMemo(() => {
    if (!data) return [] as NewsletterLite[];
    return data.filter((n) => {
      if (category) {
        const normalized = category.toLowerCase().replace(/ /g, "_");
        if (n.category !== normalized) return false;
      }
      if (start) {
        const sd = new Date(start);
        if (new Date(n.received_at) < sd) return false;
      }
      if (end) {
        const ed = new Date(end);
        ed.setDate(ed.getDate() + 1);
        if (new Date(n.received_at) >= ed) return false;
      }
      return true;
    });
  }, [data, category, start, end]);
  return { data: filtered, isFetching } as const;
};

export const useCategories = () =>
  useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<string[]>>("/ingest/categories");
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
  });

export const useExtractAll = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<{ count: number }>>(
        "/ingest/extract_all"
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["newsletters"] });
    },
  });
};

export const useVectorizeAll = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ApiResponse<{ count: number }>>(
        "/ingest/vectorize_all"
      );
      if (!data.success) throw new Error(data.error);
      return data.data!;
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["newsletters"] });
    },
  });
};
