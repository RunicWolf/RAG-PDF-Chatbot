# RAG PDF Chatbot

Chat with your PDFs using FastAPI + React + LangChain (OpenAI) + FAISS.

## Stack
- **Frontend:** React (Vite) + Tailwind
- **Backend:** FastAPI (Python)
- **AI:** LangChain + OpenAI (embeddings + chat)
- **Vector DB:** FAISS (local, file-based)
- **Deploy targets:** Vercel (frontend), Docker (backend)

## Project Structure
rag-pdf-chatbot/
  backend/
    app/
      core/        # settings, CORS
      routers/     # /api/ingest, /api/chat
      vectorstores # FAISS wrapper
    ingest.py
    main.py
    storage/faiss/   # FAISS index (after ingest)
    data/uploads/    # uploaded PDFs
    requirements.txt
  frontend/
    src/
      components/Upload.tsx
      components/Chat.tsx
      lib/api.ts

## Prereqs
- Python 3.10+ (you have 3.13)
- Node 18+ (you have v22)
- OpenAI API key

## Setup
```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Root .env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Frontend
cd ../frontend
npm i

# RUN

## Backend (from backend/)
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn app.main:app --reload --port 8000

## Frontend (from frontend/)
npm run dev

```bash
Visit: http://localhost:5173

#API

##POST /api/ingest

###Multipart form upload:

curl -F "files=@sample.pdf" http://127.0.0.1:8000/api/ingest

##POST /api/chat

###Ask questions:

curl -H "Content-Type: application/json" ^
  -d '{"question":"What does the sample PDF say?","k":4}' ^
  http://127.0.0.1:8000/api/chat

#Troubleshooting

422 / missing body → PowerShell quoting (use Invoke-RestMethod or JSON file).

CORS errors → Ensure .env CORS_ORIGINS includes frontend origin.

Empty answers → Delete backend/storage/faiss/index/ and re-ingest.

#Roadmap

Pinecone cloud vector DB

Dockerize backend

Vercel deploy frontend

Streaming answers & richer source viewer
