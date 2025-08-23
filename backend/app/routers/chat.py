from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import hashlib

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

from app.core.config import settings
# NOTE: in a later step well swap these for a store factory (FAISS or Pinecone)
from app.vectorstores.store import get_store_wrapper, get_embeddings

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    question: str
    k: int = 4
    return_debug: bool = False

class Source(BaseModel):
    page: int
    page_content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    debug_context: Optional[str] = None

SYSTEM_PROMPT = (
    "You are a helpful assistant that must answer using only the provided CONTEXT.\n"
    "Rules:\n"
    "1) If the CONTEXT contains an obvious short phrase (<= 5 words) that answers the question, REPEAT IT VERBATIM.\n"
    "2) Always include a citation like [p=<page>] using 1-based page numbers when answering.\n"
    "3) Only say I don't know. if the answer truly is not present in CONTEXT.\n"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Question: {question}\n\nCONTEXT:\n{context}")
])

def _get_retriever(k: int):
    embeddings = get_embeddings(api_key=settings.OPENAI_API_KEY or "", model=settings.EMBEDDING_MODEL)
    store = FAISSWrapper(embeddings).load()
    return store.as_retriever(search_kwargs={"k": k})

def _hash_key(doc: Document) -> str:
    # Dedup by (page, normalized text)
    page = int(doc.metadata.get("page", 0))
    text = (doc.page_content or "").strip()
    return hashlib.sha1(f"{page}|{text}".encode("utf-8")).hexdigest()

def _dedupe(docs: List[Document]) -> List[Document]:
    seen = set()
    out: List[Document] = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        key = _hash_key(d)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out

def _format_context(docs: List[Document]) -> Tuple[str, List[Source]]:
    blocks = []
    srcs: List[Source] = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        page0 = int(d.metadata.get("page", 0))
        page1 = page0 + 1
        blocks.append(f"[p={page1}] {text}")
        srcs.append(Source(page=page1, page_content=text, metadata=d.metadata or {}))
    return ("\n\n".join(blocks) if blocks else "(no context found)"), srcs

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    retriever = _get_retriever(req.k)
    docs = retriever.get_relevant_documents(req.question)
    docs = _dedupe(docs)
    context, sources = _format_context(docs)

    llm = ChatOpenAI(
        model=settings.CHAT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0
    )
    messages = prompt.format_messages(question=req.question, context=context)
    result = llm.invoke(messages)

    return ChatResponse(
        answer=result.content,
        sources=sources,
        debug_context=context if req.return_debug else None
    )
def _get_retriever(k: int):
    embeddings = get_embeddings()
    wrapper = get_store_wrapper(embeddings)
    store = wrapper.load()
    return store.as_retriever(search_kwargs={"k": k})
