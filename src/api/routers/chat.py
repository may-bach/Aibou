from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import asyncio
import json

from src.db.session import get_db, AsyncSessionLocal
from src.models.user import User
from src.models.memory import Conversation, Message
from src.schemas.chat import ChatRequest
from src.services.memory import extract_and_store_memory, get_rag_context, generate_conversation_title

from src.agents.graph import aibou_swarm
from src.agents.state import AibouState

class ConnectionManager:
    def __init__(self):
        # Maps user_id to an active WebSocket connection
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()


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


# Global map to store active generation tasks so we can cancel them
active_tasks: dict[int, asyncio.Task] = {}

async def process_chat_message(user_id: int, content: str, conversation_id: int | None, is_edit: bool = False, message_id_to_edit: int | None = None):
    """Business logic for generating a response, wrapped as an async task."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                await manager.send_personal_message({"type": "error", "message": "User not found"}, user_id)
                return

            is_new_conversation = not bool(conversation_id)
            current_chat = None

            if conversation_id:
                conv = await db.execute(
                    select(Conversation).where(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user.id
                    )
                )
                current_chat = conv.scalars().first()
                if not current_chat:
                    await manager.send_personal_message({"type": "error", "message": "Conversation not found"}, user_id)
                    return
            else:
                current_chat = Conversation(user_id=user.id, title="New Chat")
                db.add(current_chat)
                await db.flush()
                
            # If editing, delete the edited message and all subsequent messages
            if is_edit and message_id_to_edit:
                target = await db.execute(select(Message).where(Message.id == message_id_to_edit))
                target_msg = target.scalars().first()
                if target_msg:
                    # Delete this message and everything after it in this conversation
                    await db.execute(
                        Message.__table__.delete()
                        .where(Message.conversation_id == current_chat.id)
                        .where(Message.created_at >= target_msg.created_at)
                    )
                    await db.flush()

            user_msg = Message(conversation_id=current_chat.id, role="user", content=content)
            db.add(user_msg)
            await db.flush()

            asyncio.create_task(extract_and_store_memory(content))

            history_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == current_chat.id)
                .order_by(Message.id.asc())
            )
            db_history = history_result.scalars().all()

            prior_messages = db_history[:-1]
            history_lines = []
            for msg in prior_messages:
                speaker = "User" if msg.role == "user" else "Aibou"
                history_lines.append(f"{speaker}: {msg.content}")

            injected_context = await get_rag_context(content, n_results=5)

            system_parts = []
            if history_lines:
                system_parts.append("CONVERSATION HISTORY (for context only):\n" + "\n\n".join(history_lines))
            if injected_context:
                system_parts.append("RECALLED MEMORIES:\n" + injected_context)

            langchain_messages = []
            if system_parts:
                langchain_messages.append(SystemMessage(content="\n\n---\n\n".join(system_parts)))

            langchain_messages.append(HumanMessage(content=content))

            initial_state: AibouState = {
                "messages": langchain_messages,
                "artifacts": {}, 
                "current_agent": "Supervisor",
                "current_code": "",
                "execution_output": "",
                "retry_count": 0,
                "requires_human_approval": False,
                "next_route": ""
            }

            print(f"\n[WEBSOCKET] Streaming LangGraph Swarm for user {user_id}...\n")

            final_state = None
            try:
                async for output in aibou_swarm.astream(initial_state):
                    # Check for cancellation before processing output
                    if asyncio.current_task().cancelled():
                        break
                        
                    node_name = list(output.keys())[0]
                    final_state = output[node_name]
                    
                    await manager.send_personal_message({
                        "type": "status",
                        "node": node_name
                    }, user_id)
            except asyncio.CancelledError:
                print(f"[WEBSOCKET] Generation task cancelled for user {user_id}")
                await manager.send_personal_message({
                    "type": "complete",
                    "conversation_id": current_chat.id,
                    "message": "⚠️ *Generation stopped manually.*",
                    "user_message_id": user_msg.id,
                    "ai_message_id": None
                }, user_id)
                raise # Re-raise to cleanly abort the task
            except Exception as e:
                await db.rollback()
                await manager.send_personal_message({"type": "error", "message": f"Agent pipeline failed: {str(e)}"}, user_id)
                return

            if not final_state or "messages" not in final_state:
                await manager.send_personal_message({"type": "error", "message": "Failed to resolve swarm state"}, user_id)
                return

            final_ai_message = final_state["messages"][-1].content
            
            ai_msg = Message(conversation_id=current_chat.id, role="assistant", content=final_ai_message)
            db.add(ai_msg)
            await db.flush()

            generated_title: str | None = None
            if is_new_conversation and not is_edit:
                generated_title = await generate_conversation_title(content)
                current_chat.title = generated_title

            await db.commit()

            await manager.send_personal_message({
                "type": "complete",
                "conversation_id": current_chat.id,
                "message": final_ai_message,
                "title": generated_title,
                "artifacts": final_state.get("artifacts", {}),
                "agent_path": final_state.get("current_agent"),
                "user_message_id": user_msg.id,
                "ai_message_id": ai_msg.id
            }, user_id)
            
    except asyncio.CancelledError:
        pass # Expected on cancel
    except Exception as e:
        print(f"[ERROR] processing chat: {e}")
    finally:
        # Cleanup the active task reference
        if user_id in active_tasks:
            del active_tasks[user_id]


@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            msg_type = payload.get("type", "message")
            
            if msg_type == "stop":
                if user_id in active_tasks:
                    print(f"[WEBSOCKET] Kill signal received for user {user_id}. Cancelling task...")
                    active_tasks[user_id].cancel()
                continue
                
            content = payload.get("content")
            conversation_id = payload.get("conversation_id")
            
            if msg_type == "edit":
                if user_id in active_tasks:
                    active_tasks[user_id].cancel()
                message_id_to_edit = payload.get("message_id")
                if not message_id_to_edit or not content:
                    continue
                task = asyncio.create_task(process_chat_message(user_id, content, conversation_id, is_edit=True, message_id_to_edit=message_id_to_edit))
                active_tasks[user_id] = task
                
            elif msg_type == "message":
                if not content:
                    continue
                # If there's an existing task, let it run or cancel it?
                # Standard practice: cancel existing generation on new prompt
                if user_id in active_tasks:
                    active_tasks[user_id].cancel()
                    
                task = asyncio.create_task(process_chat_message(user_id, content, conversation_id))
                active_tasks[user_id] = task

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        if user_id in active_tasks:
            active_tasks[user_id].cancel()
        print(f"[WEBSOCKET] User {user_id} disconnected.")