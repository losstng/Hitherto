"use client";
import React, { createContext, useState, useContext } from "react";
import { ChatMessage } from "@/lib/types";

export interface ChatCtx {
  messageId: string;
  chunks: string[];
}

interface State {
  context: ChatCtx | null;
  setContext: (c: ChatCtx) => void;
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
  const [context, setContext] = useState<ChatCtx | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const pushMessage = (m: ChatMessage) => setMessages((msgs) => [...msgs, m]);
  return (
    <Ctx.Provider value={{ context, setContext, messages, pushMessage }}>
      {children}
    </Ctx.Provider>
  );
}
