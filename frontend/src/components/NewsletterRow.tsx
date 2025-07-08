// src/components/NewsletterRow.tsx
"use client";
import { useExtract, useChunk, useEmbed } from "@/app/actions/useProcess";
import { NewsletterLite } from "@/lib/types";
import { useChatContext } from "./ChatProvider";
import { api } from "@/lib/api";
import { useState } from "react";

export default function NewsletterRow({ n }: { n: NewsletterLite }) {
  const extract = useExtract(n.message_id);
  const chunk = useChunk(n.message_id);
  const embed = useEmbed(n.message_id);
  const { setContext, pushMessage } = useChatContext();
  const [raw, setRaw] = useState<string | null>(null);
  const [category, setCategory] = useState(n.category ?? "");

  return (
    <> 
    <tr className="border-b">
      <td className="p-2">{n.title}</td>
      <td className="p-2">{category}</td>
      <td className="p-2">{new Date(n.received_at).toLocaleString()}</td>
      <td className="p-2 space-x-1">
        <button
          onClick={() =>
            extract.mutate(undefined, {
              onSuccess: (data) => setCategory(data.category),
            })
          }
          className="btn"
        >
          Extract
        </button>
        <button
          onClick={async () => {
            await chunk.mutateAsync();
            await embed.mutateAsync();
          }}
          disabled={!extract.isSuccess}
          className="btn"
        >
          Vector
        </button>
        <button
          onClick={async () => {
            const { data } = await api.get(`/ingest/raw_text/${n.message_id}`);
            const text = data.data?.text ?? "";
            setRaw(text);
            if (data.success) {
              pushMessage({
                id: `${Date.now()}-raw`,
                role: "assistant",
                text,
                timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              });
            }
          }}
          disabled={!extract.isSuccess}
          className="btn"
        >
          Raw Text
        </button>
        <button
          onClick={async () => {
            const { data } = await api.get(`/ingest/chunked_text/${n.message_id}`);
            if (data.success) setContext({ messageId: n.message_id, chunks: data.data.chunks });
          }}
          disabled={!embed.isSuccess}
          className="btn"
        >
          Select
        </button>
      </td>
    </tr>
    {raw && (
      <tr>
        <td colSpan={4} className="p-2 bg-gray-50 text-sm whitespace-pre-wrap">
          {raw}
        </td>
      </tr>
    )}
    </>
  );
}
