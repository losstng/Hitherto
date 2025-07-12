"use client";
import { useMemo } from "react";
import { useStockQuotes } from "@/hooks/useStocks";

const DEFAULT_TICKERS = [
  "TSLA",
  "GLOB",
  "MRVL",
  "NVDA",
  "INOD",
  "PLTR",
  "DAVE",
  "HAG.DE",
];

export default function StockPrices() {
  const { data, isLoading } = useStockQuotes(DEFAULT_TICKERS);
  const sortedData = useMemo(
    () =>
      data ? [...data].sort((a, b) => a.symbol.localeCompare(b.symbol)) : [],
    [data]
  );

  return (
    <div className="text-sm border-b px-4 py-2 space-y-1">
      {isLoading && <p>Loading stocks…</p>}
      {sortedData.map((q) => (
        <div key={q.symbol} className="flex justify-between">
          <span>{q.symbol}</span>
          {q.error ? (
            <span className="text-red-600">err</span>
          ) : (
            <span
              className={
                q.change_percent && q.change_percent < 0
                  ? "text-red-600"
                  : "text-green-600"
              }
            >
              {q.price !== null ? q.price.toFixed(2) : "-"}
              {q.change_percent !== null && (
                <> ({q.change_percent.toFixed(2)}%)</>
              )}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

