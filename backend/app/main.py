from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import cors_origins_list
from app.routers import ingest as ingest_router
from app.routers import chat as chat_router

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

# Routers
app.include_router(ingest_router.router)
app.include_router(chat_router.router)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/stats")
def stats():
    # very light stats for now (extend later if you want)
    return {"vector_db": settings.VECTOR_DB, "embedding_model": settings.EMBEDDING_MODEL, "chat_model": settings.CHAT_MODEL}
