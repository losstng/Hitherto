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
  const { context, toggleContext, pushMessage } = useChatContext();
  const [category, setCategory] = useState(n.category ?? "");
  const [hasText, setHasText] = useState(!!n.has_text);
  const [vectorized, setVectorized] = useState(!!n.vectorized);

  const ensureExtracted = async () => {
    try {
      await extract.mutateAsync(undefined, {
        onSuccess: (data) => {
          setCategory(data.category);
          setHasText(true);
        },
      });
    } catch (_) {
      // ignore errors - backend handles idempotency
    }
  };

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
              onSuccess: (data) => {
                setCategory(data.category);
                setHasText(true);
              },
            })
          }
          className="btn"
          //disabled={hasText}
        >
          Extract {hasText && "✓"}
        </button>
        <button
          onClick={async () => {
            await ensureExtracted();
            await chunk.mutateAsync();
            await embed.mutateAsync(undefined, {
              onSuccess: () => setVectorized(true),
            });
          }}
          className="btn"
          //disabled={vectorized}
        >
          Vector {vectorized && "✓"}
        </button>
        <button
          onClick={async () => {
            await ensureExtracted();
            const { data } = await api.get(`/ingest/raw_text/${n.message_id}`);
            const chunks: string[] = data.data?.chunks ?? [];
            const text = chunks.join("\n\n");
            if (data.success) {
              pushMessage({
                id: `${Date.now()}-raw`,
                role: "assistant",
                text,
                timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              });
            }
          }}
          className="btn"
        >
          Raw Text
        </button>
        <button
          onClick={async () => {
            const selected = context.some((c) => c.messageId === n.message_id);
            if (selected) {
              toggleContext({ messageId: n.message_id, title: n.title, chunks: [], category: n.category, receivedAt: n.received_at });
              return;
            }
            await ensureExtracted();
            await chunk.mutateAsync();
            const { data } = await api.get(`/ingest/chunked_text/${n.message_id}`);
            if (data.success)
              toggleContext({ messageId: n.message_id, title: n.title, chunks: data.data.chunks, category: n.category, receivedAt: n.received_at });
          }}
          className="btn"
        >
          {context.some((c) => c.messageId === n.message_id) ? "Deselect" : "Select"}
        </button>
      </td>
    </tr>
    </>
  );
}
