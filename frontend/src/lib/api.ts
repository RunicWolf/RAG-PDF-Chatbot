const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

export type ChatSource = { page: number; page_content: string; metadata: Record<string, any> };
export type ChatResponse = { answer: string; sources: ChatSource[]; debug_context?: string };

export async function uploadPdfs(files: File[]): Promise<{ added_documents: number; files: string[] }> {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  const res = await fetch(`${API_BASE}/api/ingest`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function ask(question: string, k = 4, return_debug = false): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, k, return_debug }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
