import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface StockQuote {
  symbol: string;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  error?: string;
}

export const useStockQuotes = (tickers: string[]) =>
  useQuery({
    queryKey: ["stock_quotes", ...tickers],
    queryFn: async () => {
      const { data } = await api.get("/stocks/quotes", {
        params: { tickers: tickers.join(",") },
      });
      return data.data as StockQuote[];
    },
    refetchInterval: 5000, // 5 seconds
  });

