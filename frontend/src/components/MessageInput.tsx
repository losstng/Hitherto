"use client";
import React, { useState, useRef, FormEvent } from "react";

interface Props {
  onSend: (text: string, mode: string) => void;
}

export default function MessageInput({ onSend }: Props) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState("llm");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text.trim(), mode);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (text.trim()) {
        onSend(text.trim(), mode);
        setText("");
        if (textareaRef.current) textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  return (
    <form onSubmit={submit} className="sticky bottom-0 p-3 bg-white border-t flex items-end gap-2">
      <select value={mode} onChange={(e) => setMode(e.target.value)} className="border rounded px-1 text-sm">
        <option value="extracted">extracted</option>
        <option value="vector">vector</option>
        <option value="rag">rag</option>
        <option value="llm">llm</option>
      </select>
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Type a message…"
        className="flex-1 resize-none border rounded p-2 text-sm focus:outline-none"
      />
      <button type="submit" className="bg-blue-600 text-white px-3 py-1 rounded">
        Send
      </button>
    </form>
  );
}
