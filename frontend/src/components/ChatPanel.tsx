"use client";
import React from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ChatMessage, ApiResponse, ContextDoc } from "@/lib/types";
import { ChatHistory, MessageInput } from ".";
import { useChatContext } from ".";
import { useLLMChat } from "@/hooks/useLLMChat";

interface AskResp {
  reply: string;
  source?: string;
}

export default function ChatPanel() {
  const { context, filters, messages, pushMessage, clearContext } = useChatContext();
  const [mode, setMode] = React.useState("llm");

  const {
    messages: llmMessages,
    send: llmSend,
    loading: llmLoading,
    reset: llmReset
  } = useLLMChat();

  interface AskPayload {
    query: string;
    mode: string;
    chunks?: string[];
  }

const ask = useMutation({
    mutationFn: async ({ text, mode }: { text: string; mode: string }) => {
      const payload: AskPayload = { query: text, mode };
      let chunks: string[] = [];

      if (context.length > 0) {
        const ids = context.map((c) => c.messageId);
        const { data } = await api.post<ApiResponse<ContextDoc[]>>('/context', {
          query: text,
          categories: [],
          start_date: null,
          end_date: null,
          message_ids: ids,
          k: 5,
        });
        if (data.success && data.data) chunks = data.data.map((d) => d.page_content);
      } else if (filters.category || filters.start || filters.end) {
        const { data } = await api.post<ApiResponse<ContextDoc[]>>('/context', {
          query: text,
          categories: filters.category ? [filters.category] : [],
          start_date: filters.start || null,
          end_date: filters.end || null,
          k: 5,
        });
        if (data.success && data.data) chunks = data.data.map((d) => d.page_content);
      } else {
        const { data } = await api.post<ApiResponse<ContextDoc[]>>('/context', {
          query: text,
          categories: [],
          start_date: null,
          end_date: null,
          k: 5,
        });
        if (data.success && data.data) chunks = data.data.map((d) => d.page_content);
      }

      if (chunks.length > 0) payload.chunks = chunks;

      const { data } = await api.post<ApiResponse<AskResp>>('/ask', payload);
      return data;
    },
    onSuccess: (data) => {
      const reply: ChatMessage = {
        id: `${Date.now()}-a`,
        role: "assistant",
        text: data.data?.reply ?? "",
        source: data.data?.source,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      pushMessage(reply);
    }
  });

  // Updated: For LLM, send context IDs and filters too
  const handleSend = (text: string, sendMode: string) => {
    setMode(sendMode);
    if (sendMode === "llm") {
      const contextIds = context.map(c => c.messageId);
      llmSend(text, contextIds, filters);
    } else {
    const userMsg: ChatMessage = {
      id: `${Date.now()}-u`,
      role: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    pushMessage(userMsg);
      ask.mutate({ text, mode: sendMode });
    }
  };

  React.useEffect(() => {
    if (mode === "llm" && llmMessages.length === 0) {
      llmReset();
    }
    // eslint-disable-next-line
  }, [mode, llmMessages.length]);

  const displayedMessages = mode === "llm" ? llmMessages : messages;
  const loading = mode === "llm" ? llmLoading : ask.isPending;

  return (
    <div className="flex flex-col h-full w-full bg-white border-l shadow-lg overflow-hidden">
      {context.length > 0 && (
        <div className="flex items-center px-3 py-2 text-xs border-b bg-gray-50">
          <span className="flex-1">
            Context:
            {context
              .map((c) =>
                `${c.title} [${c.tokenCount ?? 0} tokens]${c.oc ? " (OC)" : ""}`
              )
              .join(", ")}
          </span>
          <button onClick={clearContext} className="text-blue-600 underline ml-2">
            Clear
          </button>
        </div>
      )}
      <ChatHistory messages={displayedMessages} loading={loading} />
      <MessageInput onSend={handleSend} />
    </div>
  );
}