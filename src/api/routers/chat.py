from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message
from src.schemas.chat import ChatRequest
from src.services.memory import extract_and_store_memory, get_rag_context

from src.agents.graph import aibou_swarm
from src.agents.state import AibouState


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
    db_history = history_result.scalars().all()
    
    langchain_messages = []
    for msg in db_history:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        else:
            langchain_messages.append(AIMessage(content=msg.content))

    injected_context = await get_rag_context(request.content, n_results=5)
    if injected_context:
        memory_prompt = SystemMessage(content=f"RECALLED MEMORIES:\n{injected_context}")
        langchain_messages.insert(-1, memory_prompt)

    initial_state: AibouState = {
        "messages": langchain_messages,
        "artifacts": {}, 
        "current_agent": "Supervisor",
        "current_code": "",
        "execution_output": "",
        "retry_count": 0,
        "requires_human_approval": False
    }

    print("\n[FASTAPI] Handing over execution to LangGraph Swarm...\n")

    try:
        final_state = await aibou_swarm.ainvoke(initial_state)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {str(e)}")

    final_ai_message = final_state["messages"][-1].content
    
    ai_msg = Message(conversation_id=current_chat.id, role="assistant", content=final_ai_message)
    db.add(ai_msg)
    await db.commit()

    return {
        "conversation_id": current_chat.id,
        "Aibou": final_ai_message,
        "artifacts": final_state.get("artifacts", {}),
        "agent_path": final_state.get("current_agent")
    }