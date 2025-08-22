import { useState } from "react";
import { ask } from "../lib/api";
import type { ChatResponse } from "../lib/api";




type Msg = { role: "user" | "assistant"; content: string; sources?: ChatResponse["sources"]; debug?: string };

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const question = q.trim();
    if (!question) return;
    setMessages((m) => [...m, { role: "user", content: question }]);
    setQ("");
    setBusy(true);
    try {
      const res = await ask(question, 3, false);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, sources: res.sources, debug: res.debug_context }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", content: e.message || "Error" }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="space-y-4 max-h-[60vh] overflow-y-auto mb-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div
              className={`inline-block p-3 rounded-2xl ${
                m.role === "user" ? "bg-zinc-900 text-white" : "bg-zinc-100"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.role === "assistant" && m.sources && (
                <div className="mt-2 text-xs text-zinc-600">
                  <p className="font-medium mb-1">Sources</p>
                  <ul className="list-disc ml-5 space-y-1">
                    {m.sources.map((s, idx) => (
                      <li key={idx}>
                        [p={String((s.metadata?.page ?? 0) + 1)}] {String(s.page_content).slice(0, 160)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          placeholder="Ask something about your PDFs"
          className="flex-1 border rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-zinc-300"
        />
        <button
          onClick={send}
          disabled={busy}
          className="px-4 py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-50"
        >
          {busy ? "" : "Send"}
        </button>
      </div>
    </div>
  );
}
