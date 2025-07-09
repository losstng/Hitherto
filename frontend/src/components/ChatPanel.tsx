"use client";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import ChatHistory from "./ChatHistory";
import MessageInput from "./MessageInput";
import { useChatContext } from "./ChatProvider";

interface AskResp {
  reply: string;
  source?: string;
}

export default function ChatPanel() {
  const { context, messages, pushMessage } = useChatContext();

  interface AskPayload {
    query: string;
    mode: string;
    chunks?: string[];
  }

  const ask = useMutation({
    mutationFn: async ({ text, mode }: { text: string; mode: string }) => {
      const payload: AskPayload = { query: text, mode };
      if (context) payload.chunks = context.chunks;
      const { data } = await api.post("/ask", payload);
      return data as { success: boolean; data: AskResp };
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

  const handleSend = (text: string, mode: string) => {
    const userMsg: ChatMessage = {
      id: `${Date.now()}-u`,
      role: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    pushMessage(userMsg);
    ask.mutate({ text, mode });
  };

  return (
    <div className="flex flex-col h-full w-full bg-white border-l shadow-lg overflow-hidden">
      {context && (
        <div className="px-3 py-2 text-xs border-b bg-gray-50">Context: {context.messageId}</div>
      )}
      <ChatHistory messages={messages} loading={ask.isPending} />
      <MessageInput onSend={handleSend} />
    </div>
  );
}
