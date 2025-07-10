"use client";
import React, { createContext, useState, useContext } from "react";
import { ChatMessage } from "@/lib/types";

export interface ChatCtxItem {
  messageId: string;
  title: string;
  chunks: string[];
  category?: string | null;
  receivedAt?: string;
  oc?: boolean;
}

interface Filters {
  category: string;
  start: string;
  end: string;
}

interface State {
  context: ChatCtxItem[];
  toggleContext: (c: ChatCtxItem) => void;
  filters: Filters;
  setFilters: (f: Partial<Filters>) => void;
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
  const [filters, setFiltersState] = useState<Filters>({ category: "", start: "", end: "" });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const pushMessage = (m: ChatMessage) => setMessages((msgs) => [...msgs, m]);
  const computeOC = (item: ChatCtxItem, f: Filters) => {
    if (f.category && item.category && item.category !== f.category) return true;
    if (f.start) {
      const sd = new Date(f.start);
      if (item.receivedAt && new Date(item.receivedAt) < sd) return true;
    }
    if (f.end) {
      const ed = new Date(f.end);
      ed.setDate(ed.getDate() + 1);
      if (item.receivedAt && new Date(item.receivedAt) >= ed) return true;
    }
    return false;
  };
  const toggleContext = (c: ChatCtxItem) =>
    setContext((ctx) => {
      const exists = ctx.some((i) => i.messageId === c.messageId);
      if (exists) return ctx.filter((i) => i.messageId !== c.messageId);
      const oc = computeOC(c, filters);
      return [...ctx, { ...c, oc }];
    });
  const setFilters = (f: Partial<Filters>) =>
    setFiltersState((flts) => ({ ...flts, ...f }));

  React.useEffect(() => {
    setContext((ctx) => ctx.map((i) => ({ ...i, oc: computeOC(i, filters) })));
  }, [filters]);
  return (
    <Ctx.Provider value={{ context, toggleContext, filters, setFilters, messages, pushMessage }}>
      {children}
    </Ctx.Provider>
  );
}
