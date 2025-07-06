export interface NewsletterMeta {
  title: string;
  message_id: string;
  category: string | null;
  received_at: string | null;
  has_text: boolean;
  has_chunks: boolean;
}

/** call POST /ingest/bloomberg_reload */
const API = process.env.NEXT_PUBLIC_API;

export async function reloadBloomberg(): Promise<NewsletterMeta[]> {
  const res = await fetch(`${API}/ingest/bloomberg_reload`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data as NewsletterMeta[];
}

export async function extractText(id: string) {
  const res = await fetch(`${API}/ingest/extract_text/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function chunkText(id: string) {
  const res = await fetch(`${API}/ingest/chunk/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}

export async function embedNewsletter(id: string) {
  const res  = await fetch(`${API}/ingest/embed/${id}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data;
}
