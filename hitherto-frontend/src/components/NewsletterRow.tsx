// src/components/NewsletterRow.tsx
"use client";
import {
  useExtract,
  useChunk,
  useEmbed,
  useTokenize,
} from "@/hooks/useProcess";
import { NewsletterLite } from "@/lib/types";

export default function NewsletterRow({ n }: { n: NewsletterLite }) {
  const extract  = useExtract(n.message_id);
  const chunk    = useChunk(n.message_id);
  const embed    = useEmbed(n.message_id);
  const tokenize = useTokenize(n.message_id);

  return (
    <tr className="border-b">
      <td className="p-2">{n.title}</td>
      <td className="p-2">{new Date(n.received_at).toLocaleString()}</td>
      <td className="p-2 space-x-1">
        <button onClick={() => extract.mutate()} className="btn">Extract</button>
        <button onClick={() => chunk.mutate()}   disabled={!extract.isSuccess} className="btn">Chunk</button>
        <button onClick={() => embed.mutate()}   disabled={!chunk.isSuccess}   className="btn">Embed</button>
        <button onClick={() => tokenize.mutate()}disabled={!embed.isSuccess}   className="btn">Tokenize</button>
      </td>
    </tr>
  );
}
