"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import ChatHistory from "@/components/ChatHistory";
import MessageInput from "@/components/MessageInput";

interface AskResp {
  reply: string;
  source?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const ask = useMutation({
    mutationFn: async ({ text, mode }: { text: string; mode: string }) => {
      const { data } = await api.post("/ask", { query: text, mode });
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
      setMessages((msgs) => [...msgs, reply]);
    }
  });

  const handleSend = (text: string, mode: string) => {
    const userMsg: ChatMessage = {
      id: `${Date.now()}-u`,
      role: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };
    setMessages((msgs) => [...msgs, userMsg]);
    ask.mutate({ text, mode });
  };

  return (
    <main className="flex flex-col h-[calc(100vh-4rem)]">
      <ChatHistory messages={messages} loading={ask.isPending} />
      <MessageInput onSend={handleSend} />
    </main>
  );
}
