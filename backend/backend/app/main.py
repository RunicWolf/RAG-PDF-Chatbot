from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import cors_origins_list

app = FastAPI(title="RAG PDF Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
