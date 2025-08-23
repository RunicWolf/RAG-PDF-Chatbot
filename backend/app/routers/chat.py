from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import hashlib
import re
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

from app.core.config import settings
from app.vectorstores.store import get_store_wrapper, get_embeddings

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    question: str
    k: int = 4
    return_debug: bool = False
    filename: Optional[str] = None  # optional per-question scope
    mode: str = "auto"              # "auto" or "cross"

class Source(BaseModel):
    page: int
    page_content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    debug_context: Optional[str] = None

# ---------- Prompts (Fix 2) ----------
FACTOID_PROMPT_TXT = (
    "You must answer using only the provided CONTEXT.\n"
    "If CONTEXT is non-empty, try to extract the most relevant span. "
    "Only say 'I don't know.' if CONTEXT is literally empty.\n"
    "Rules:\n"
    "1) If a short phrase (<= 6 words) in CONTEXT answers, repeat it verbatim.\n"
    "2) Always include a citation like [p=<page>].\n"
)

SUMMARY_PROMPT_TXT = (
    "You are to write a concise, faithful summary using only the CONTEXT.\n"
    "If CONTEXT is non-empty, you must produce a summary. "
    "Only say 'I don't know.' if CONTEXT is literally empty.\n"
    "Rules:\n"
    "1) 3–5 sentences max, neutral tone.\n"
    "2) Cite where appropriate using [p=<page>].\n"
)

CROSS_PROMPT_TXT = (
    "You are comparing and analyzing content from MULTIPLE documents using only the CONTEXT.\n"
    "Rules:\n"
    "1) If the question asks for similarities/differences, compare across documents.\n"
    "2) Always cite filenames and page numbers, e.g. [filename, p=12].\n"
    "3) Only say 'I don't know.' if CONTEXT is literally empty.\n"
)
# -------------------------------------

factoid_template = ChatPromptTemplate.from_messages([
    ("system", FACTOID_PROMPT_TXT),
    ("human", "Question: {question}\n\nCONTEXT:\n{context}")
])

summary_template = ChatPromptTemplate.from_messages([
    ("system", SUMMARY_PROMPT_TXT),
    ("human", "Summarize:\n\n{question}\n\nCONTEXT:\n{context}")
])

cross_template = ChatPromptTemplate.from_messages([
    ("system", CROSS_PROMPT_TXT),
    ("human", "Question: {question}\n\nCONTEXT (from multiple docs):\n{context}")
])

def _classify(question: str) -> str:
    q = question.lower().strip()
    if q.startswith("summar") or "summary" in q or "summarise" in q:
        return "summary"
    if len(q) <= 80 or re.match(r"^(what|when|who|where|which|quote)\b", q):
        return "factoid"
    return "summary"

def _get_store():
    embeddings = get_embeddings()
    wrapper = get_store_wrapper(embeddings)
    return wrapper.load()

def _retrieval(store, question: str, kind: str, k: int) -> List[Document]:
    # Prefer MMR to reduce redundancy
    if hasattr(store, "max_marginal_relevance_search"):
        fetch_k = max(8, k * 4) if kind == "summary" else max(6, k * 3)
        return store.max_marginal_relevance_search(
            question, k=k, fetch_k=fetch_k, lambda_mult=0.3
        )
    retriever = store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": max(8, k * 4) if kind == "summary" else max(6, k * 3),
            "lambda_mult": 0.3
        }
    )
    return retriever.get_relevant_documents(question)

def _hash_key(doc: Document) -> str:
    page = int((doc.metadata or {}).get("page", 0))
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

def _format_context(docs: List[Document], include_filename: bool = False) -> Tuple[str, List[Source]]:
    blocks = []
    srcs: List[Source] = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        page0 = int((d.metadata or {}).get("page", 0))
        page1 = page0 + 1
        fname = (d.metadata or {}).get("filename") or (d.metadata or {}).get("source") or "document"
        if include_filename:
            blocks.append(f"[{fname}, p={page1}] {text}")
        else:
            blocks.append(f"[p={page1}] {text}")
        md = dict(d.metadata or {})
        md["filename"] = fname
        srcs.append(Source(page=page1, page_content=text, metadata=md))
    return ("\n\n".join(blocks) if blocks else "(no context found)"), srcs

# ---------- exact-quote helpers (Fix 3 relaxed) ----------
def _looks_like_quote_question(q: str) -> bool:
    q = q.lower()
    return any(kw in q for kw in [
        "what does", "what did", "exact words", "quote", "verbatim", "say?"
    ])

def _short_text(t: str) -> bool:
    # allow a concise single sentence to be quoted
    return len(t.strip()) <= 200 and "\n" not in t
# --------------------------------------------------------

# ---------- file auto-scope (Fix 1) ----------
def _best_filename_by_grouping(docs: List[Document]) -> Optional[str]:
    """
    Group retrieved docs by filename and score each group by inverse-rank (1/(rank+1)).
    Pick the filename with the highest total. Works even without similarity scores.
    """
    if not docs:
        return None
    scores: Dict[str, float] = defaultdict(float)
    for rank, d in enumerate(docs):
        fname = (d.metadata or {}).get("filename") or (d.metadata or {}).get("source") or "document"
        scores[fname] += 1.0 / (rank + 1.0)
    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best
# --------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    kind = _classify(req.question)
    k = req.k if req.k else (3 if kind == "factoid" else 8)

    store = _get_store()
    docs = _retrieval(store, req.question, kind, k)

    # --- Mode handling ---
    mode = (req.mode or "auto").lower().strip()
    if req.filename:
        # explicit filename scope always wins (case-insensitive)
        want = req.filename.strip().lower()
        docs = [d for d in docs if ((d.metadata or {}).get("filename", "").strip().lower() == want)]
    else:
        if mode == "auto":
            # pick the best single file
            best = _best_filename_by_grouping(docs)
            if best:
                docs = [d for d in docs if ((d.metadata or {}).get("filename") == best)]
        elif mode == "cross":
            # keep multiple files (no further filter)
            pass
        else:
            # unknown mode -> fallback to auto
            best = _best_filename_by_grouping(docs)
            if best:
                docs = [d for d in docs if ((d.metadata or {}).get("filename") == best)]
    # ---------------------

    docs = _dedupe(docs)
    include_filename = (mode == "cross" and not req.filename)
    context, sources = _format_context(docs, include_filename=include_filename)

    # exact-quote fallback
    if sources and _looks_like_quote_question(req.question):
        for s in sources:
            if _short_text(s.page_content):
                # if we showed filename in context, keep simple page-only cite here
                return ChatResponse(
                    answer=f"{s.page_content} [p={s.page}]",
                    sources=sources,
                    debug_context=context if req.return_debug else None,
                )

    if context == "(no context found)":
        return ChatResponse(
            answer="I don't know.",
            sources=[],
            debug_context=context if req.return_debug else None
        )

    # Pick template
    if mode == "cross" and not req.filename:
        template = cross_template
    else:
        template = factoid_template if kind == "factoid" else summary_template

    llm = ChatOpenAI(model=settings.CHAT_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0)
    messages = template.format_messages(question=req.question, context=context)
    result = llm.invoke(messages)

    return ChatResponse(answer=result.content, sources=sources, debug_context=context if req.return_debug else None)
