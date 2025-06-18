export interface NewsletterMeta {
  title: string;
  message_id: string;
  category: string | null;
  received_at: string | null;
  has_text: boolean;
  has_chunks: boolean;
}

/** call POST /ingest/bloomberg_reload */
export async function reloadBloomberg(): Promise<NewsletterMeta[]> {
  const res = await fetch("/ingest/bloomberg_reload", { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data as NewsletterMeta[];
}

export async function extractText(id: string) {
  const res = await fetch(`/ingest/extract_text/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function chunkText(id: string) {
  const res = await fetch(`/ingest/chunk/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function embedNewsletter(id: string) {
  const res  = await fetch(`/ingest/embed/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}