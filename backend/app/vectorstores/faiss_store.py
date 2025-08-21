import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Storage location: backend/storage/faiss/index
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "faiss")
INDEX_PATH = os.path.join(STORAGE_DIR, "index")
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_embeddings(api_key: str, model: str):
    return OpenAIEmbeddings(api_key=api_key, model=model)

class FAISSWrapper:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def exists(self) -> bool:
        return os.path.isdir(INDEX_PATH)

    def load(self) -> FAISS:
        # Load an existing index only
        return FAISS.load_local(INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)

    def save(self, store: FAISS):
        store.save_local(INDEX_PATH)
