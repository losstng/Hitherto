"use client";
import React, { useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/types";

export default function ChatHistory({ messages, loading }: { messages: ChatMessage[]; loading?: boolean }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Ask Hitherto anything about your Bloomberg digests…
      </div>
    );
  }

  return (
    <div className="min-h-[85vh] max-h-[87vh] overflow-y-auto overflow-x-hidden p-4 space-y-3">
  {messages.map((m) => (
    <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`w-full max-w-[90%] sm:max-w-lg break-words whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
          m.role === "user" ? "bg-gray-100 text-black" : "bg-indigo-50 text-gray-900"
        }`}
      >
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
  ))}
</div>
  );
}
