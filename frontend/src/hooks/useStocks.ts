import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StockOHLCV, StockDataForDate } from "@/lib/types";

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

export const useAvailableSymbols = () =>
  useQuery({
    queryKey: ["stock_symbols"],
    queryFn: async () => {
      const { data } = await api.get("/stocks/symbols");
      return data.data as string[];
    },
  });

export const useDailyStockData = (symbol: string, startDate?: string, endDate?: string) =>
  useQuery({
    queryKey: ["daily_stock_data", symbol, startDate, endDate],
    queryFn: async () => {
      const { data } = await api.get(`/stocks/daily/${symbol}`, {
        params: { start_date: startDate, end_date: endDate },
      });
      return data.data as StockOHLCV[];
    },
    enabled: !!symbol,
  });

export const useIntradayStockData = (symbol: string, startDate?: string, endDate?: string) =>
  useQuery({
    queryKey: ["intraday_stock_data", symbol, startDate, endDate],
    queryFn: async () => {
      const { data } = await api.get(`/stocks/intraday/${symbol}`, {
        params: { start_date: startDate, end_date: endDate },
      });
      return data.data as StockOHLCV[];
    },
    enabled: !!symbol,
  });

export const useStockDataForDate = (symbol: string, date: string) =>
  useQuery({
    queryKey: ["stock_data_for_date", symbol, date],
    queryFn: async () => {
      const { data } = await api.get(`/stocks/data/${symbol}/${date}`);
      return data.data as StockDataForDate;
    },
    enabled: !!symbol && !!date,
  });

