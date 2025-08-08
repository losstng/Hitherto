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

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { method: "POST" });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data as T;
}

export const reloadBloomberg = () =>
  post<NewsletterMeta[]>("/ingest/bloomberg_reload");

export const extractText = (id: string) =>
  post(`/ingest/extract_text/${id}`);

export const chunkText = (id: string) =>
  post(`/ingest/chunk/${id}`);

export const embedNewsletter = (id: string) =>
  post(`/ingest/embed/${id}`);
