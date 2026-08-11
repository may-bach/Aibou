import asyncio
import chromadb
from chromadb.utils import embedding_functions
from openai import AsyncOpenAI
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from src.core.config import settings


EXTRACTOR_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extractor.md"
with open(EXTRACTOR_PROMPT_PATH, "r", encoding="utf-8") as file:
    EXTRACTOR_PROMPT_TEMPLATE = file.read()

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url=f"{settings.LOCAL_LLM_URL}/api/embeddings",
    model_name="nomic-embed-text",
)

chroma_client = chromadb.PersistentClient(path="./aibou_vector_db")
rag_collection = chroma_client.get_or_create_collection(
    name="aibou_memories",
    embedding_function=ollama_ef
)

extractor_llm_client = AsyncOpenAI(
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
)

async def generate_conversation_title(user_message: str) -> str:
    try:
        response = await extractor_llm_client.chat.completions.create(
            model=settings.MODEL_EXTRACTOR,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a concise 3-6 word title summarizing the user message below. "
                        "RULES:\n"
                        "1. ONLY use words relevant to the message.\n"
                        "2. No quotes, punctuation, or preamble."
                    ),
                },
                {"role": "user", "content": user_message[:400]},
            ],
            max_tokens=25,
        )
        raw = response.choices[0].message.content.strip()
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        words = clean.split()[:6]
        return " ".join(words) if words else _fallback_title(user_message)
    except Exception:
        return _fallback_title(user_message)


def _fallback_title(text: str) -> str:
    words = text.split()[:6]
    title = " ".join(words)
    return title if len(title) <= 60 else title[:57] + "…"


def split_text_into_chunks(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Split text into semantic paragraph-aware chunks with overlap for vector storage."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current_chunk) + len(p) + 2 <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(p) > chunk_size:
                # If a single paragraph is huge, split by sentences or slice
                for i in range(0, len(p), chunk_size - overlap):
                    chunks.append(p[i : i + chunk_size])
                current_chunk = ""
            else:
                current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text[:chunk_size]]


def store_document_in_rag(filename: str, text: str):
    """Chunk and store an uploaded document (PDF, Word, Text) into persistent ChromaDB memory."""
    if not text or not text.strip():
        return

    chunks = split_text_into_chunks(text)
    current_date = datetime.now().strftime("%Y-%m-%d")

    clean_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    doc_ids = []
    doc_texts = []
    doc_metas = []

    for idx, chunk in enumerate(chunks, 1):
        chunk_id = f"doc_{clean_filename}_chunk_{idx}"
        formatted_chunk = f"[Document: {filename} (Section {idx})]\n{chunk}"
        
        doc_ids.append(chunk_id)
        doc_texts.append(formatted_chunk)
        doc_metas.append({
            "source": filename,
            "type": "uploaded_document",
            "chunk_index": idx,
            "date": current_date
        })

    try:
        rag_collection.upsert(
            ids=doc_ids,
            documents=doc_texts,
            metadatas=doc_metas
        )
        print(f"\n[RAG MEMORY] Successfully indexed {len(doc_ids)} chunks from '{filename}' into vector database!\n")
    except Exception as e:
        print(f"[RAG ERROR] Failed to store document '{filename}': {e}")


async def get_rag_context(query_text: str, n_results: int = 5) -> str:
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: rag_collection.query(query_texts=[query_text], n_results=n_results)
        )
        
        context_docs = []
        if results.get("documents") and results["documents"]:
            context_docs = results["documents"][0]

        injected_context = ""
        if context_docs:
            injected_context = "\n".join(f"- {doc}" for doc in context_docs if doc.strip())
            
        return injected_context
    except Exception as e:
        print(f"[RAG QUERY ERROR]: {e}")
        return ""


async def extract_and_store_memory(user_text: str):
    if not user_text or len(user_text.strip()) < 5:
        return

    current_time = datetime.now().strftime("%A, %b %d, %Y at %I:%M %p")

    injected_context = await get_rag_context(user_text, n_results=3)
    if not injected_context:
        injected_context = "No prior context available."

    extraction_prompt = EXTRACTOR_PROMPT_TEMPLATE.format(
        context=injected_context
    )

    try:
        response = await extractor_llm_client.chat.completions.create(
            model=settings.MODEL_EXTRACTOR,
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": user_text}
            ]
        )

        ai_text = response.choices[0].message.content
        clean_text = re.sub(r'<think>.*?</think>', '', ai_text, flags=re.DOTALL).strip()
        
        # Clean markdown formatting around NONE
        clean_stripped = re.sub(r'[*`_#]', '', clean_text).strip().upper()

        if clean_stripped and clean_stripped != "NONE" and "NO EXTRACTED MEMORY" not in clean_stripped and "NO MEMORY" not in clean_stripped:
            memory_id = f"fact_{uuid.uuid4()}"
            formatted_memory = f"[{current_time}] {clean_text}"

            rag_collection.add(
                documents=[formatted_memory],
                metadatas=[{"date": datetime.now().strftime("%Y-%m-%d"), "type": "auto_fact"}],
                ids=[memory_id]
            )
            print(f"\n[AIBOU LEARNED MEMORY]: {formatted_memory}\n")

    except Exception as e:
        print(f"\nMemory extraction failed silently: {e}\n")