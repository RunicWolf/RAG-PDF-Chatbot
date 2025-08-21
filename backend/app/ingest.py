import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.vectorstores.faiss_store import FAISSWrapper, get_embeddings

# Data dirs
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Splitter defaults
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
    # Load and split
    docs = _load_pdfs(paths)
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings(api_key=settings.OPENAI_API_KEY or "", model=settings.EMBEDDING_MODEL)
    wrapper = FAISSWrapper(embeddings)

    if wrapper.exists():
        store = wrapper.load()
        store.add_documents(chunks)
    else:
        # First time: build index directly from documents (no dummy vectors)
        store = FAISS.from_documents(chunks, embeddings)

    wrapper.save(store)
    return len(chunks)
