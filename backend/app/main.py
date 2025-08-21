from fastapi import FastAPI

app = FastAPI(title="RAG PDF Chatbot API")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
