from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import re
from datetime import datetime
import uuid

from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message


router = APIRouter()

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "core_aibou.md"
with open(PROMPT_PATH, "r", encoding="utf-8") as file:
    AIBOU_PROMPT = file.read()

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

chroma_client = chromadb.PersistentClient(path="./aibou_vector_db")
rag_collection = chroma_client.get_collection(
    name="personal_projects", 
    embedding_function=ollama_ef
)

class ChatRequest(BaseModel):
    user_id: int
    content: str
    conversation_id: int | None = None

async def extract_and_store_memory(user_text: str):
    current_time = datetime.now().strftime("%A, %b %d, %Y at %I:%M %p")
    
    extraction_prompt = f"""
    You are a silent memory extractor. Analyze the user's message: "{user_text}"
    Did the user state a fact, preference, routine, or current state about themselves?
    If YES: Summarize it into a single, concise third-person sentence. (e.g., "The user is feeling tired after the gym.")
    If NO: Output exactly the word "NONE" and nothing else.
    Do not output <think> tags. Just the summary or NONE.
    """
    
    try:
        response = await client.chat.completions.create(
            model="deepseek-r1:14b", 
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        # Clean the response
        ai_text = response.choices[0].message.content
        clean_text = re.sub(r'<think>.*?</think>', '', ai_text, flags=re.DOTALL).strip()
        
        # If it found a memory, save it to ChromaDB forever!
        if clean_text != "NONE" and clean_text != "":
            memory_id = f"log_{uuid.uuid4()}"
            formatted_memory = f"[{current_time}] {clean_text}"
            
            rag_collection.add(
                documents=[formatted_memory],
                metadatas=[{"date": datetime.now().strftime("%Y-%m-%d"), "type": "auto_memory"}],
                ids=[memory_id]
            )
            print(f"\n🧠 AIBOU LEARNED A NEW MEMORY: {formatted_memory}\n")
    except Exception as e:
        print(f"\n⚠️ Memory extraction failed silently: {e}\n")


@router.post("/chat/")
async def chat_with_aibou(request: ChatRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.conversation_id:
        conv = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id,Conversation.user_id == user.id)
        )

        current_chat = conv.scalars().first()

        if not current_chat:
            raise HTTPException(status_code = 404,detail="Conversation not found.")
    
    else:
        current_chat = Conversation(user_id=user.id, title="New Chat")
        db.add(current_chat)
        await db.flush() 

    user_msg = Message(conversation_id=current_chat.id, role="user", content=request.content)
    db.add(user_msg)
    await db.flush()

    background_tasks.add_task(extract_and_store_memory, request.content)

    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == current_chat.id)
        .order_by(Message.id.asc())
    )
    chat_history = history_result.scalars().all()

    rag_results = rag_collection.query(
        query_texts=[request.content],
        n_results=1 
    )
    
    injected_context = ""
    if rag_results['documents'] and rag_results['documents'][0]:
        injected_context = rag_results['documents'][0][0]

    system_prompt = AIBOU_PROMPT
    if injected_context:
        system_prompt += f"\n\n--- RELEVANT CONTEXT FROM USER'S FILES ---\n{injected_context}"

    messages_payload = [
        {"role": "system", "content": system_prompt}
    ]
    
    for msg in chat_history:
        if msg.role == "assistant":
            clean_content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL)
            clean_content = clean_content.replace("</think>", "").strip()
            
            messages_payload.append({"role": msg.role, "content": clean_content})
        else:
            messages_payload.append({"role": msg.role, "content": msg.content})

    response = await client.chat.completions.create(
        model="deepseek-r1:14b", 
        messages=messages_payload 
    )
    
    ai_text = response.choices[0].message.content

    ai_msg = Message(conversation_id=current_chat.id, role="assistant", content=ai_text)
    db.add(ai_msg)
    
    await db.commit()

    return {
        "conversation_id": current_chat.id,
        "Aibou_response": ai_text
    }