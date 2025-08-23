import os
import shutil
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

# Tuned splitter: larger chunks, small overlap → better semantic coherence
SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=150,
    separators=["\n\n", "\n", " ", ""],
)

def _load_pdfs(paths: List[str]):
    docs = []
    for p in paths:
        loader = PyPDFLoader(p)
        loaded = loader.load()
        # add filename into metadata early
        fname = os.path.basename(p)
        for d in loaded:
            d.metadata = d.metadata or {}
            d.metadata["filename"] = fname
        docs.extend(loaded)
    return docs

def _clear_faiss_if_exists(embeddings) -> None:
    """
    Remove the FAISS index directory if it exists.
    This ensures a fresh index for every ingest (useful in dev).
    """
    from app.vectorstores.faiss_store import FAISSWrapper  # local import to avoid hard dep
    faiss = FAISSWrapper(embeddings)
    if getattr(faiss, "exists", None) and faiss.exists():
        # index_path is defined by FAISSWrapper; fall back to storage path if needed
        index_path = getattr(faiss, "index_path", os.path.join(BASE_DIR, "storage", "faiss", "index"))
        shutil.rmtree(index_path, ignore_errors=True)

def ingest_pdf_paths(paths: List[str], replace: bool = False) -> int:
    """
    Ingest the given PDF file paths into the configured vector store.

    replace=True (default) clears the FAISS index before ingesting to avoid mixing
    with previously uploaded documents. Set replace=False to append.
    """
    docs = _load_pdfs(paths)
    chunks = SPLITTER.split_documents(docs)

    embeddings = get_embeddings()
    wrapper = get_store_wrapper(embeddings)

    vector_db = (settings.VECTOR_DB or "").lower()

    # FAISS (local, file-based)
    if vector_db == "faiss":
        from app.vectorstores.faiss_store import FAISSWrapper
        faiss = FAISSWrapper(embeddings)

        # Replace mode: clear old index first
        if replace:
            _clear_faiss_if_exists(embeddings)
            store = FAISS.from_documents(chunks, embeddings)
            faiss.save(store)
        else:
            # Append mode
            if faiss.exists():
                store = faiss.load()
                store.add_documents(chunks)
                faiss.save(store)
            else:
                store = FAISS.from_documents(chunks, embeddings)
                faiss.save(store)

    # Pinecone (or any remote backend via your factory)
    else:
        # For Pinecone, "replace" is typically handled at the index level.
        # Here we simply add documents; if you want hard replace, drop/recreate the index in your Pinecone wrapper.
        wrapper.add_documents(chunks)

    return len(chunks)
