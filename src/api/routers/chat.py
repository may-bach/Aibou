from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message
from src.schemas.chat import ChatRequest
from src.services.memory import extract_and_store_memory, get_rag_context, generate_conversation_title

from src.agents.graph import aibou_swarm
from src.agents.state import AibouState


router = APIRouter(prefix="/chat", tags=["Chat"])


# ── GET: list all conversations for a user ────────────────────────────────────
@router.get("/conversations/{user_id}")
async def list_conversations(user_id: int, db: AsyncSession = Depends(get_db)):
    """Return all conversations for a user, newest first."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    convs_result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = convs_result.scalars().all()

    output = []
    for conv in conversations:
        count_result = await db.execute(
            select(func.count()).where(Message.conversation_id == conv.id)
        )
        msg_count = count_result.scalar() or 0

        first_msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id, Message.role == "user")
            .order_by(Message.id.asc())
            .limit(1)
        )
        first_msg = first_msg_result.scalars().first()

        output.append({
            "id": conv.id,
            "title": conv.title or (first_msg.content[:60] if first_msg else "New Chat"),
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "message_count": msg_count,
        })

    return output


# ── GET: messages in a conversation ──────────────────────────────────────────
@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """Return all messages in a conversation, oldest first."""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
    )
    messages = msgs_result.scalars().all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]


# ── DELETE: remove a conversation and all its messages ───────────────────────
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """Hard-delete a conversation and all its messages from the database."""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)          # cascade="all, delete-orphan" removes messages too
    await db.commit()
    return {"ok": True}


# ── POST: send a message ──────────────────────────────────────────────────────
@router.post("/")
async def chat_with_aibou(request: ChatRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_new_conversation = not bool(request.conversation_id)

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

    # Load conversation history (excluding the new user message we just flushed)
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == current_chat.id)
        .order_by(Message.id.asc())
    )
    db_history = history_result.scalars().all()

    # Build a formatted history string (all messages EXCEPT the latest user one)
    prior_messages = db_history[:-1]
    history_lines = []
    for msg in prior_messages:
        speaker = "User" if msg.role == "user" else "Aibou"
        history_lines.append(f"{speaker}: {msg.content}")

    # Inject RAG context
    injected_context = await get_rag_context(request.content, n_results=5)

    # Build the system message combining history + memories
    system_parts = []
    if history_lines:
        system_parts.append("CONVERSATION HISTORY (for context only):\n" + "\n\n".join(history_lines))
    if injected_context:
        system_parts.append("RECALLED MEMORIES:\n" + injected_context)

    langchain_messages = []
    if system_parts:
        langchain_messages.append(SystemMessage(content="\n\n---\n\n".join(system_parts)))

    # Only the new user message goes in as a live message
    langchain_messages.append(HumanMessage(content=request.content))

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

    # Generate and persist a relevant title for brand-new conversations
    generated_title: str | None = None
    if is_new_conversation:
        generated_title = await generate_conversation_title(request.content)
        current_chat.title = generated_title

    await db.commit()

    return {
        "conversation_id": current_chat.id,
        "Aibou": final_ai_message,
        "title": generated_title,          # None for existing conversations
        "artifacts": final_state.get("artifacts", {}),
        "agent_path": final_state.get("current_agent")
    }