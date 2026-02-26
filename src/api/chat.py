from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI
from pathlib import Path
import re
from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message

#creating the router
router = APIRouter()

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "core_aibou.md"
with open(PROMPT_PATH, "r", encoding="utf-8") as file:
    AIBOU_PROMPT = file.read()

class ChatRequest(BaseModel):
    user_id: int
    content: str
    conversation_id: int | None = None

@router.post("/chat/")
async def chat_with_aibou(request: ChatRequest, db: AsyncSession = Depends(get_db)):

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

    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == current_chat.id)
        .order_by(Message.id.asc())
    )
    chat_history = history_result.scalars().all()

    messages_payload = [
        {"role": "system", "content":AIBOU_PROMPT}
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