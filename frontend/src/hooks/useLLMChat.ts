import { useState } from "react";
import axios from "axios";
import { ChatMessage } from "@/lib/types";
import { api } from "@/lib/api";

const LLM_BASE = "http://127.0.0.1:1234/v1";
const LLM_MODEL = "openai/gpt-oss-20b";

// Added: Types for optional arguments
type ContextDoc = { page_content: string };
type FilterOptions = { category?: string; start?: string; end?: string };
type LLMChatOptions = {
  contextIds?: string[];
  filters?: FilterOptions;
  query?: string;
};

export function useLLMChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Reset chat history
  const reset = () => setMessages([]);

  // Main send
  const send = async (
    text: string,
    contextIds: string[] = [],
    filters: FilterOptions = {}
  ) => {
    const userMsg: ChatMessage = {
      id: `${Date.now()}-u`,
      role: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    // --- RAG: retrieve context if present ---
    let chunkContents: string[] = [];
    try {
      if (contextIds.length > 0) {
        // Fetch context by selected messages
        const { data } = await api.post<{ success: boolean; data: ContextDoc[] }>("/context", {
          query: text,
          categories: [],
          start_date: null,
          end_date: null,
          message_ids: contextIds,
          k: 5,
        });
        if (data.success) chunkContents = data.data.map((d) => d.page_content);
      } else if (filters.category || filters.start || filters.end) {
        // Fetch context with filters
        const { data } = await api.post<{ success: boolean; data: ContextDoc[] }>("/context", {
          query: text,
          categories: filters.category ? [filters.category] : [],
          start_date: filters.start || null,
          end_date: filters.end || null,
          k: 5,
        });
        if (data.success) chunkContents = data.data.map((d) => d.page_content);
      }
    } catch (fetchErr) {
      console.error("Error fetching context for LLM", fetchErr);
    }

    // --- Compose messages for LLM API ---
    const chatHistory = [...messages, userMsg].map(m => ({ role: m.role, content: m.text }));
    let llmMessages: Array<{ role: "user" | "assistant" | "system"; content: string }> = chatHistory;
    if (chunkContents.length > 0) {
      const contextMessage = {
        role: "system" as const,
        content: `Here are some context excerpts for the following chat.\n${chunkContents.join("\n---\n")}`
      };
      llmMessages = [contextMessage, ...chatHistory];
    }

    try {
      const resp = await axios.post(`${LLM_BASE}/chat/completions`, {
        model: LLM_MODEL,
        messages: llmMessages,
        max_tokens: -1,
        temperature: 0.7,
        stream: false
      });
      const content = resp.data?.choices?.[0]?.message?.content || "[No LLM reply]";
      const assistantMsg: ChatMessage = {
        id: `${Date.now()}-a`,
        role: "assistant",
        text: content,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e: any) {
      console.error('LLM API error', e, e?.response?.data);
      setMessages(prev => [...prev, {
        id: `${Date.now()}-e`,
        role: "assistant",
        text: "[LLM error: could not get response]",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }]);
    } finally {
      setLoading(false);
    }
  };

  return {
    messages,
    send,
    loading,
    reset
  };
}
