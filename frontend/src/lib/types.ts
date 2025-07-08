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
}

export type ReloadResp  = { new_entries: number };
export type ExtractResp = {
  message_id: string;
  title: string;
  category: string;
  extracted_text_preview: string;
};

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp?: string;
  source?: string;
}
