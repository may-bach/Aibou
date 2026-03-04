from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message
from src.schemas.chat import ChatRequest
from src.services.memory import extract_and_store_memory, get_rag_context
from src.services.llm import generate_chat_response
from src.agents.router import route_prompt

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
async def chat_with_aibou(request: ChatRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.conversation_id:
        conv = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id
            )
        )
        current_chat = conv.scalars().first()
        
        if not current_chat:
            raise HTTPException(status_code=404, detail="Conversation not found.")
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

    target_model = await route_prompt(request.content)
    print(f"\n[ROUTER] Assigned prompt to model: {target_model}\n")

    injected_context = get_rag_context(request.content, n_results=5)
    
    ai_text = await generate_chat_response(
        chat_history=chat_history,
        injected_context=injected_context,
        model_name=target_model
    )

    ai_msg = Message(conversation_id=current_chat.id, role="assistant", content=ai_text)
    db.add(ai_msg)
    await db.commit()

    return {
        "conversation_id": current_chat.id,
        "Aibou": ai_text
    }