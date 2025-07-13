"use client";
import React, { useEffect, useRef, useState } from "react";
import { VariableSizeList as List } from "react-window";
import { ChatMessage } from "@/lib/types";

export default function ChatHistory({ messages, loading }: { messages: ChatMessage[]; loading?: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<List>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) setHeight(containerRef.current.clientHeight);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const itemCount = messages.length + (loading ? 1 : 0);

  useEffect(() => {
    listRef.current?.scrollToItem(itemCount - 1);
  }, [messages, loading, itemCount]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Ask Hitherto anything about your Bloomberg digests…
      </div>
    );
  }

  const getItemSize = (index: number) => {
    if (index === messages.length) return 40;
    const len = messages[index].text.length;
    return Math.min(200, Math.max(60, Math.ceil(len / 50) * 24 + 36));
  };

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (index === messages.length) {
      return loading ? (
        <div style={style} className="flex justify-start">
          <div className="bg-indigo-50 text-gray-900 max-w-lg rounded-lg px-3 py-2 text-sm">Hitherto is thinking…</div>
        </div>
      ) : (
        <div style={style} />
      );
    }
    const m = messages[index];
    return (
      <div style={{ ...style, paddingBottom: "0.5rem" }} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
        <div className={`max-w-lg rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-gray-100 text-black" : "bg-indigo-50 text-gray-900"}`}>
          <p>{m.text}</p>
          <button
            onClick={() => navigator.clipboard.writeText(m.text)}
            className="mt-1 text-xs text-blue-500 hover:underline"
          >
            Copy
          </button>
          {(m.timestamp || m.source) && (
            <div className="mt-1 text-xs text-gray-500 flex justify-between">
              {m.timestamp && <span>{m.timestamp}</span>}
              {m.source && <span>source: {m.source}</span>}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div ref={containerRef} className="flex-1 overflow-hidden p-4">
      {height > 0 && (
        <List
          ref={listRef}
          height={height}
          width="100%"
          itemCount={itemCount}
          itemSize={getItemSize}
        >
          {Row}
        </List>
      )}
    </div>
  );
}
