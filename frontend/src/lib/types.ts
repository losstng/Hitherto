// src/lib/types.ts
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface NewsletterLite {
  title: string;
  message_id: string;
  received_at: string;
  category?: string | null;
  has_text?: boolean;
  has_chunks?: boolean;
  vectorized?: boolean;
}

export type ReloadResp  = { new_entries: number };
export type ExtractResp = {
  message_id: string;
  title: string;
  category: string;
  extracted_text_preview: string;
};

export type ChunkResp = {
  message_id: string;
  has_chunks: boolean;
};

export interface EmbedResp {
  message_id: string;
  embedded?: boolean;
  already_embedded?: boolean;
  vectorized: boolean;
}

export type TokenResp = {
  message_id: string;
  token_count: number;
};

export interface ContextDoc {
  page_content: string;
  metadata: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp?: string;
  source?: string;
}

// Stock data types
export interface StockOHLCV {
  date: string;
  datetime: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  time?: string; // For intraday data
}

export interface StockDataForDate {
  symbol: string;
  date: string;
  daily: StockOHLCV | null;
  intraday: StockOHLCV[];
}

export interface TimelineItem {
  date: string;
  newsletters: NewsletterLite[];
  stockData: StockDataForDate[];
}
