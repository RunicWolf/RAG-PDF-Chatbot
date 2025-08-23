from app.core.config import settings
from app.vectorstores.faiss_store import FAISSWrapper, get_embeddings as get_openai_embeddings

# Lazy import to avoid requiring pinecone unless used
def get_store_wrapper(embeddings):
    if (settings.VECTOR_DB or "").lower() == "pinecone":
        from app.vectorstores.pinecone_store import PineconeWrapper
        return PineconeWrapper(embeddings)
    return FAISSWrapper(embeddings)

def get_embeddings():
    return get_openai_embeddings(api_key=settings.OPENAI_API_KEY or "", model=settings.EMBEDDING_MODEL)
