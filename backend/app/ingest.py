import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from app.vectorstores.store import get_store_wrapper, get_embeddings
from app.core.config import settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""],
)

def _load_pdfs(paths: List[str]):
    docs = []
    for p in paths:
        loader = PyPDFLoader(p)
        docs.extend(loader.load())
    return docs

def ingest_pdf_paths(paths: List[str]) -> int:
    docs = _load_pdfs(paths)
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings()
    wrapper = get_store_wrapper(embeddings)

    # For FAISS we need to either load or create; for Pinecone we just add
    if (settings.VECTOR_DB or "").lower() == "faiss":
        from app.vectorstores.faiss_store import FAISSWrapper
        faiss = FAISSWrapper(embeddings)
        if faiss.exists():
            store = faiss.load()
            store.add_documents(chunks)
            faiss.save(store)
        else:
            store = FAISS.from_documents(chunks, embeddings)
            faiss.save(store)
    else:
        wrapper.add_documents(chunks)

    return len(chunks)
