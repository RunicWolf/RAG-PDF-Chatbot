import { useState } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";

export default function App() {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | "ALL">("ALL");

  return (
    <div className="min-h-screen p-6 max-w-5xl mx-auto">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">RAG PDF Chatbot</h1>
        <p className="text-sm text-zinc-600">Upload PDFs · Ask questions · Get cited answers</p>
      </header>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="p-4 bg-white rounded-2xl shadow">
            <h2 className="font-semibold mb-2">Upload PDFs</h2>
            <Upload
              onIngest={(ingested) => {
                // ingested.files from backend
                const names = ingested.files as string[];
                setFiles(names);
                // auto-select the last uploaded file for convenience
                if (names.length > 0) setSelectedFile(names[names.length - 1]);
              }}
            />
            {files.length > 0 && (
              <p className="text-xs text-zinc-500 mt-2">
                Ingested {files.length} file{files.length > 1 ? "s" : ""}: {files.join(", ")}
              </p>
            )}
          </div>
        </div>

        <div className="md:col-span-2">
          <div className="p-4 bg-white rounded-2xl shadow">
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-semibold">Chat</h2>
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-500">Scope:</span>
                <select
                  className="text-sm border rounded-lg px-2 py-1"
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value as any)}
                >
                  <option value="ALL">All documents</option>
                  {files.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
            </div>
            <Chat filename={selectedFile === "ALL" ? undefined : selectedFile} />
          </div>
        </div>
      </div>
    </div>
  );
}
