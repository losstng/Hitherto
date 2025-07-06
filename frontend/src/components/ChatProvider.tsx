"use client";
import React, { createContext, useState, useContext } from "react";

export interface ChatCtx {
  messageId: string;
  chunks: string[];
}

interface State {
  context: ChatCtx | null;
  setContext: (c: ChatCtx) => void;
}

const Ctx = createContext<State | undefined>(undefined);

export function useChatContext() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("ChatContext missing");
  return ctx;
}

export default function ChatProvider({ children }: { children: React.ReactNode }) {
  const [context, setContext] = useState<ChatCtx | null>(null);
  return <Ctx.Provider value={{ context, setContext }}>{children}</Ctx.Provider>;
}
