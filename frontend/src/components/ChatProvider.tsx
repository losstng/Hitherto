"use client";
import React, { createContext, useState, useContext } from "react";
import { ChatMessage } from "@/lib/types";

export interface ChatCtxItem {
  messageId: string;
  title: string;
  chunks: string[];
}

interface State {
  context: ChatCtxItem[];
  toggleContext: (c: ChatCtxItem) => void;
  messages: ChatMessage[];
  pushMessage: (m: ChatMessage) => void;
}

const Ctx = createContext<State | undefined>(undefined);

export function useChatContext() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("ChatContext missing");
  return ctx;
}

export default function ChatProvider({ children }: { children: React.ReactNode }) {
  const [context, setContext] = useState<ChatCtxItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const pushMessage = (m: ChatMessage) => setMessages((msgs) => [...msgs, m]);
  const toggleContext = (c: ChatCtxItem) =>
    setContext((ctx) => {
      const exists = ctx.some((i) => i.messageId === c.messageId);
      if (exists) return ctx.filter((i) => i.messageId !== c.messageId);
      return [...ctx, c];
    });
  return (
    <Ctx.Provider value={{ context, toggleContext, messages, pushMessage }}>
      {children}
    </Ctx.Provider>
  );
}
