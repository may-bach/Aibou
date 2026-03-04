import chromadb
from chromadb.utils import embedding_functions
from openai import AsyncOpenAI
import re
import uuid
from datetime import datetime
from pathlib import Path
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

def get_rag_context(query_text: str, n_results: int = 5) -> str:
    try:
        results = rag_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        context_docs = []
        if results.get("documents"):
            context_docs = results["documents"][0]

        injected_context = ""
        if context_docs:
            injected_context = "\n".join(f"- {doc}" for doc in context_docs)
            
        return injected_context
    except Exception:
        return ""

async def extract_and_store_memory(user_text: str):
    current_time = datetime.now().strftime("%A, %b %d, %Y at %I:%M %p")

    injected_context = get_rag_context(user_text, n_results=3)
    
    if injected_context == "":
        injected_context = "No prior context available."

    extraction_prompt = EXTRACTOR_PROMPT_TEMPLATE.format(
        context=injected_context
    )

    try:
        response = await extractor_llm_client.chat.completions.create(
            model=settings.MODEL_EXTRACTOR  ,
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": user_text}
            ]
        )

        ai_text = response.choices[0].message.content
        clean_text = re.sub(r'<think>.*?</think>', '', ai_text, flags=re.DOTALL).strip()

        if clean_text.upper() != "NONE":
            if clean_text != "":
                memory_id = f"log_{uuid.uuid4()}"
                formatted_memory = f"[{current_time}] {clean_text}"

                rag_collection.add(
                    documents=[formatted_memory],
                    metadatas=[{"date": datetime.now().strftime("%Y-%m-%d"), "type": "auto_memory"}],
                    ids=[memory_id]
                )
                print(f"\nAIBOU LEARNED A NEW MEMORY: {formatted_memory}\n")

    except Exception as e:
        print(f"\nMemory extraction failed silently: {e}\n")