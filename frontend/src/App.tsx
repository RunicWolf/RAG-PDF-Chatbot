import Upload from "./components/Upload";
import Chat from "./components/Chat";

export default function App() {
  return (
    <div className="min-h-screen p-6 max-w-5xl mx-auto">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">RAG PDF Chatbot</h1>
        <p className="text-sm text-zinc-600">Upload PDFs  Ask questions  Get cited answers</p>
      </header>
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="p-4 bg-white rounded-2xl shadow">
            <h2 className="font-semibold mb-2">Upload PDFs</h2>
            <Upload />
          </div>
        </div>
        <div className="md:col-span-2">
          <div className="p-4 bg-white rounded-2xl shadow">
            <h2 className="font-semibold mb-2">Chat</h2>
            <Chat />
          </div>
        </div>
      </div>
    </div>
  );
}
