from typing import List
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from langchain.docstore.document import Document

class PineconeWrapper:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        # Create index if not exists
        assert settings.PINECONE_INDEX, "PINECONE_INDEX not set"
        if settings.PINECONE_INDEX not in [idx.name for idx in self.pc.list_indexes()]:
            self.pc.create_index(
                name=settings.PINECONE_INDEX,
                dimension=1536,  # text-embedding-3-small dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD or "aws",
                    region=settings.PINECONE_REGION or "us-east-1",
                ),
            )
        self.index = self.pc.Index(settings.PINECONE_INDEX)

    def as_retriever(self, search_kwargs=None):
        store = PineconeVectorStore(index_name=settings.PINECONE_INDEX, embedding=self.embeddings)
        return store.as_retriever(search_kwargs=search_kwargs or {"k": 4})

    # For ingest
    def add_documents(self, docs: List[Document]):
        store = PineconeVectorStore(index_name=settings.PINECONE_INDEX, embedding=self.embeddings)
        store.add_documents(docs)

    # FAISS compatibility no-ops
    def load(self):
        return self

    def save(self, _store):
        return
