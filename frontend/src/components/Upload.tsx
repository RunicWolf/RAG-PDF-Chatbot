import { uploadPdfs } from "../lib/api";
import { useRef, useState } from "react";


export default function Upload() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState<string>("");

  const pick = () => inputRef.current?.click();

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setBusy(true);
    try {
      const res = await uploadPdfs(files);
      setLast(`Ingested ${res.added_documents} chunks from ${res.files.join(", ")}`);
    } catch (e: any) {
      setLast(e.message || "Upload failed");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="application/pdf"
        className="hidden"
        onChange={onChange}
      />
      <button
        onClick={pick}
        disabled={busy}
        className="px-4 py-2 rounded-xl bg-zinc-900 text-white disabled:opacity-50"
      >
        {busy ? "Uploading" : "Choose PDFs"}
      </button>
      {last && <p className="text-xs text-zinc-600 mt-2">{last}</p>}
    </div>
  );
}
