"use client";
import React, { useState, useMemo } from "react";
import { useNewsletters, useAvailableSymbols, useStockDataForDate } from "@/hooks";
import { NewsletterLite, TimelineItem } from "@/lib/types";
import CandlestickChart from "./CandlestickChart";
import { NewsletterRow } from ".";

interface NewsletterTimelineProps {
  startDate?: string;
  endDate?: string;
  selectedSymbols?: string[];
}

export default function NewsletterTimeline({ 
  startDate, 
  endDate, 
  selectedSymbols = ["NVDA", "TSLA", "MRVL"] 
}: NewsletterTimelineProps) {
  const [expandedDates, setExpandedDates] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'daily' | 'intraday'>('daily');
  
  const { data: newsletters, isLoading: newslettersLoading } = useNewsletters();
  const { data: availableSymbols } = useAvailableSymbols();

  // Group newsletters by date
  const newslettersByDate = useMemo(() => {
    if (!newsletters) return {};
    
    const grouped: Record<string, NewsletterLite[]> = {};
    
    newsletters.forEach(newsletter => {
      const date = new Date(newsletter.received_at).toISOString().split('T')[0];
      
      // Filter by date range if provided
      if (startDate && date < startDate) return;
      if (endDate && date > endDate) return;
      
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(newsletter);
    });
    
    return grouped;
  }, [newsletters, startDate, endDate]);

  // Get unique dates sorted
  const dates = useMemo(() => {
    return Object.keys(newslettersByDate).sort().reverse(); // Most recent first
  }, [newslettersByDate]);

  const toggleDate = (date: string) => {
    const newExpanded = new Set(expandedDates);
    if (newExpanded.has(date)) {
      newExpanded.delete(date);
    } else {
      newExpanded.add(date);
    }
    setExpandedDates(newExpanded);
  };

  if (newslettersLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-lg">Loading timeline...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-bold">Newsletter & Stock Timeline</h2>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium">View:</label>
            <select 
              value={viewMode} 
              onChange={(e) => setViewMode(e.target.value as 'daily' | 'intraday')}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="daily">Daily Charts</option>
              <option value="intraday">Intraday Charts</option>
            </select>
          </div>
        </div>
        
        <div className="text-sm text-gray-600">
          Showing {dates.length} days with newsletters
        </div>
      </div>

      {/* Symbol selection */}
      <div className="p-4 bg-blue-50 rounded-lg">
        <h3 className="font-medium mb-2">Stocks to Display:</h3>
        <div className="flex flex-wrap gap-2">
          {selectedSymbols.map(symbol => (
            <span key={symbol} className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-sm">
              {symbol}
            </span>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-6">
        {dates.map(date => {
          const dayNewsletters = newslettersByDate[date] || [];
          const isExpanded = expandedDates.has(date);
          
          return (
            <TimelineDayItem
              key={date}
              date={date}
              newsletters={dayNewsletters}
              symbols={selectedSymbols}
              isExpanded={isExpanded}
              onToggle={() => toggleDate(date)}
              viewMode={viewMode}
            />
          );
        })}
      </div>

      {dates.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No newsletters found for the selected date range.
        </div>
      )}
    </div>
  );
}

interface TimelineDayItemProps {
  date: string;
  newsletters: NewsletterLite[];
  symbols: string[];
  isExpanded: boolean;
  onToggle: () => void;
  viewMode: 'daily' | 'intraday';
}

function TimelineDayItem({ 
  date, 
  newsletters, 
  symbols, 
  isExpanded, 
  onToggle, 
  viewMode 
}: TimelineDayItemProps) {
  const formattedDate = new Date(date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
      {/* Day header */}
      <div 
        className="p-4 bg-gray-50 border-b cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{formattedDate}</h3>
            <p className="text-sm text-gray-600">
              {newsletters.length} newsletter{newsletters.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">
              {isExpanded ? '−' : '+'}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Stock charts for this date */}
          <div>
            <h4 className="font-medium mb-3">Stock Performance - {date}</h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {symbols.map(symbol => (
                <StockChartForDate
                  key={symbol}
                  symbol={symbol}
                  date={date}
                  viewMode={viewMode}
                />
              ))}
            </div>
          </div>

          {/* Newsletters for this date */}
          <div>
            <h4 className="font-medium mb-3">Newsletter{newsletters.length !== 1 ? 's' : ''}</h4>
            <div className="space-y-2">
              {newsletters.map(newsletter => (
                <div key={newsletter.message_id} className="p-3 bg-gray-50 rounded border">
                  <div className="text-sm font-medium text-blue-600 mb-1">
                    {newsletter.title}
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    {newsletter.category && (
                      <span className="bg-gray-200 px-2 py-1 rounded mr-2">
                        {newsletter.category}
                      </span>
                    )}
                    {new Date(newsletter.received_at).toLocaleTimeString()}
                  </div>
                  {/* You could add newsletter content preview here */}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface StockChartForDateProps {
  symbol: string;
  date: string;
  viewMode: 'daily' | 'intraday';
}

function StockChartForDate({ symbol, date, viewMode }: StockChartForDateProps) {
  const { data, isLoading, error } = useStockDataForDate(symbol, date);
  
  if (isLoading) {
    return (
      <div className="h-48 bg-gray-100 rounded flex items-center justify-center">
        <span className="text-gray-500">Loading {symbol}...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="h-48 bg-red-50 rounded flex items-center justify-center">
        <span className="text-red-500">Error loading {symbol}</span>
      </div>
    );
  }

  const chartData = viewMode === 'daily' 
    ? (data.daily ? [data.daily] : [])
    : data.intraday;

  if (chartData.length === 0) {
    return (
      <div className="h-48 bg-gray-100 rounded flex items-center justify-center">
        <span className="text-gray-500">No {viewMode} data for {symbol}</span>
      </div>
    );
  }

  return (
    <CandlestickChart
      data={chartData}
      symbol={symbol}
      width={350}
      height={200}
    />
  );
}
