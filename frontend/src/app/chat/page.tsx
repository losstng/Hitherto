"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reloadBloomberg, extractText, chunkText, NewsletterMeta, embedNewsletter } from "./actions/useIngest";
import React from "react";

export default function Dashboard() {
  const qc = useQueryClient();

  // fetch table data
  const { data, isLoading, error } = useQuery<NewsletterMeta[]>({
    queryKey: ["bloomberg"],
    queryFn: reloadBloomberg,   // first load will also trigger scan+persist
    refetchOnWindowFocus: false,
  });

  // single-row actions
  const extractMut = useMutation({
    mutationFn: extractText,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bloomberg"] }),
  });

  const chunkMut = useMutation({
    mutationFn: chunkText,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bloomberg"] }),
  });

  const embedMut = useMutation({
    mutationFn: embedNewsletter,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bloomberg"] }),
  });

  if (isLoading) return <p className="p-4">Loading…</p>;
  if (error)   return <p className="p-4 text-red-600">Error: {(error as any).message}</p>;

  return (
    <main className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Bloomberg Newsletters</h1>

      <button
        onClick={() => qc.invalidateQueries({ queryKey: ["bloomberg"] })}
        className="mb-4 rounded bg-blue-600 text-white py-1 px-3 hover:bg-blue-700"
      >
        🔄 Reload Gmail + refresh table
      </button>

      <table className="w-full text-sm border">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 text-left">Title</th>
            <th className="p-2">Category</th>
            <th className="p-2">Received</th>
            <th className="p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {data!.map(n => (
            <tr key={n.message_id} className="border-t">
              <td className="p-2">{n.title}</td>
              <td className="p-2">{n.category ?? "—"}</td>
              <td className="p-2">{n.received_at?.slice(0, 10) ?? "—"}</td>
              <td className="p-2 space-x-2">
  <button
    disabled={n.has_text || extractMut.isPending}
    onClick={() => extractMut.mutate(n.message_id)}
    className="btn"
  >
    📄 Extract
  </button>

  <button
    disabled={!n.has_text || n.has_chunks || chunkMut.isPending}
    onClick={() => chunkMut.mutate(n.message_id)}
    className="btn"
  >
    🧩 Chunk
  </button>

  <button
    disabled={!n.has_chunks || embedMut.isPending}
    onClick={() => embedMut.mutate(n.message_id)}
    className="btn"
  >
    📦 Embed
  </button>
</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}