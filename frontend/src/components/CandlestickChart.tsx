"use client";
import React from "react";
import { StockOHLCV } from "@/lib/types";

interface CandlestickChartProps {
  data: StockOHLCV[];
  width?: number;
  height?: number;
  symbol: string;
}

export default function CandlestickChart({ 
  data, 
  width = 400, 
  height = 200, 
  symbol 
}: CandlestickChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center w-full h-32 bg-gray-100 rounded">
        <span className="text-gray-500">No data available for {symbol}</span>
      </div>
    );
  }

  // Calculate min/max values for scaling
  const prices = data.flatMap(d => [d.high, d.low]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1; // 10% padding
  
  const scaledMin = minPrice - padding;
  const scaledMax = maxPrice + padding;
  const scaledRange = scaledMax - scaledMin;

  const candleWidth = Math.max(2, width / data.length - 2);
  const chartHeight = height - 40; // Leave space for labels

  const scaleY = (price: number) => {
    return chartHeight - ((price - scaledMin) / scaledRange) * chartHeight + 20;
  };

  return (
    <div className="bg-white p-2 rounded border">
      <h4 className="text-sm font-medium mb-2">{symbol} - Candlestick Chart</h4>
      <svg width={width} height={height} className="overflow-visible">
        {/* Price grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const y = 20 + ratio * chartHeight;
          const price = scaledMax - (ratio * scaledRange);
          return (
            <g key={i}>
              <line
                x1={20}
                y1={y}
                x2={width - 20}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth={0.5}
              />
              <text
                x={5}
                y={y + 3}
                fontSize="10"
                fill="#6b7280"
                textAnchor="start"
              >
                {price.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* Candlesticks */}
        {data.map((candle, i) => {
          const x = 20 + (i * (width - 40)) / data.length;
          const isGreen = candle.close >= candle.open;
          const color = isGreen ? "#10b981" : "#ef4444";
          
          const highY = scaleY(candle.high);
          const lowY = scaleY(candle.low);
          const openY = scaleY(candle.open);
          const closeY = scaleY(candle.close);
          
          const bodyTop = Math.min(openY, closeY);
          const bodyBottom = Math.max(openY, closeY);
          const bodyHeight = Math.max(1, bodyBottom - bodyTop);

          return (
            <g key={i}>
              {/* High-Low line (wick) */}
              <line
                x1={x + candleWidth / 2}
                y1={highY}
                x2={x + candleWidth / 2}
                y2={lowY}
                stroke={color}
                strokeWidth={1}
              />
              
              {/* Open-Close body */}
              <rect
                x={x}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                fill={isGreen ? color : "white"}
                stroke={color}
                strokeWidth={1}
              />
              
              {/* Time label (show every few candles to avoid crowding) */}
              {i % Math.max(1, Math.floor(data.length / 5)) === 0 && (
                <text
                  x={x + candleWidth / 2}
                  y={height - 5}
                  fontSize="8"
                  fill="#6b7280"
                  textAnchor="middle"
                  transform={`rotate(-45, ${x + candleWidth / 2}, ${height - 5})`}
                >
                  {candle.time || new Date(candle.datetime).toLocaleDateString()}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      
      {/* Legend */}
      <div className="flex text-xs text-gray-600 mt-1 space-x-4">
        <span>Open: {data[0]?.open.toFixed(2)}</span>
        <span>Close: {data[data.length - 1]?.close.toFixed(2)}</span>
        <span>High: {Math.max(...data.map(d => d.high)).toFixed(2)}</span>
        <span>Low: {Math.min(...data.map(d => d.low)).toFixed(2)}</span>
      </div>
    </div>
  );
}
