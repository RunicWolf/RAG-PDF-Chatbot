from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

from app.core.config import settings
from app.vectorstores.faiss_store import FAISSWrapper, get_embeddings

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    question: str
    k: int = 4
    session_id: Optional[str] = None
    return_debug: bool = False  # <-- TEMP: return context back

class Source(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    debug_context: Optional[str] = None  # <-- TEMP

SYSTEM_PROMPT = (
    "You are a helpful assistant that must answer using only the provided CONTEXT.\n"
    "Rules:\n"
    "1) If the CONTEXT contains an obvious short phrase (<= 5 words) that answers the question, REPEAT IT VERBATIM with no extra words.\n"
    "2) Always include a citation like [p=<page>] using 1-based page numbers when answering.\n"
    "3) Only say “I don't know.” if the answer truly is not present in CONTEXT.\n"
)


prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Question: {question}\n\nCONTEXT:\n{context}")
])

def _retriever(k: int):
    embeddings = get_embeddings(api_key=settings.OPENAI_API_KEY or "", model=settings.EMBEDDING_MODEL)
    store = FAISSWrapper(embeddings).load()
    return store.as_retriever(search_kwargs={"k": k})

def _format_context(docs: List[Document]) -> str:
    blocks = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        page_raw = d.metadata.get("page", 0)
        try:
            page1 = int(page_raw) + 1
        except Exception:
            page1 = 1
        blocks.append(f"[p={page1}] {text}")
    return "\n\n".join(blocks) if blocks else "(no context found)"

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    retriever = _retriever(req.k)
    docs = retriever.get_relevant_documents(req.question)
    context = _format_context(docs)

    llm = ChatOpenAI(
        model=settings.CHAT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0
    )
    messages = prompt.format_messages(question=req.question, context=context)
    result = llm.invoke(messages)

    # Filter empty sources (in case any slipped in)
    clean_sources = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        clean_sources.append(Source(page_content=text, metadata=d.metadata or {}))

    return ChatResponse(
        answer=result.content,
        sources=clean_sources,
        debug_context=context if req.return_debug else None
    )
