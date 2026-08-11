from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
import asyncio
import json
import re
from pathlib import Path

from src.db.session import get_db, AsyncSessionLocal
from src.models.user import User
from src.models.memory import Conversation, Message
from src.schemas.chat import ChatRequest
from src.services.memory import extract_and_store_memory, get_rag_context, generate_conversation_title, store_document_in_rag
from src.services.document_parser import extract_text_from_file
from src.agents.tools import aibou_tools, tool_map
from src.core.config import settings

# Core personality prompt
PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "core_aibou.md"
if PROMPT_PATH.exists():
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        CORE_PROMPT = re.sub(r'<!--[\s\S]*?-->', '', file.read()).strip()

else:
    CORE_PROMPT = "You are Aibou (相棒), a sharp, casual, and intelligent AI companion."

TOOL_DIRECTIVE = """
--- LIVE TOOLS & REAL-TIME SEARCH ---
You have access to live tools:
1. `web_search`: Search the web for current events, latest sports winners/results, recent news, real-time facts, or external documentation. ALWAYS use this tool when asked about recent real-world events or sports facts beyond your static cutoff.
2. `calculate`: Use for exact arithmetic or mathematical equations.
3. `get_current_time`: Check the current date, time, or day of the week.
4. `read_local_file`: Inspect project files.

When tools return data, synthesize the results cleanly and naturally into your answer without repeating paragraphs or dumping raw JSON.
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"[WS ERROR] Failed to send to user {user_id}: {e}")

manager = ConnectionManager()

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content_bytes = await file.read()
        parsed = extract_text_from_file(content_bytes, file.filename or "uploaded_file")
        if not parsed.get("success"):
            raise HTTPException(status_code=400, detail=parsed.get("error", "Failed to parse document"))
        
        # Store chunks in chroma so memory stays across chats
        if parsed.get("text"):
            store_document_in_rag(file.filename or "uploaded_file", parsed["text"])

        return parsed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")


@router.get("/conversations/{user_id}")
async def list_conversations(user_id: int, db: AsyncSession = Depends(get_db)):
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

    await db.delete(conv)
    await db.commit()
    return {"ok": True}


# ── WEBSOCKET: High-performance direct streaming with RAG & Tools ────────────
@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            content = payload.get("content")
            conversation_id = payload.get("conversation_id")
            local_chat_id = payload.get("local_chat_id")
            attachments = payload.get("attachments", [])
            
            if not content and not attachments:
                continue

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()
                if not user:
                    await manager.send_personal_message({"type": "error", "message": "User not found"}, user_id)
                    continue

                is_new_conversation = not bool(conversation_id)

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
                        continue
                else:
                    current_chat = Conversation(user_id=user.id, title="New Chat")
                    db.add(current_chat)
                    await db.flush()

                # User display message
                display_content = content or ""
                if attachments:
                    att_names = ", ".join([a.get("filename", "file") for a in attachments])
                    if not display_content:
                        display_content = f"Uploaded document: {att_names}"
                    for att in attachments:
                        if att.get("text"):
                            store_document_in_rag(att.get("filename", "document"), att["text"])

                user_msg = Message(conversation_id=current_chat.id, role="user", content=display_content)
                db.add(user_msg)
                await db.flush()

                # Background long-term memory extraction
                asyncio.create_task(extract_and_store_memory(display_content))

                # Load conversation history for context
                history_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == current_chat.id)
                    .order_by(Message.id.asc())
                )
                db_history = history_result.scalars().all()

                prior_messages = db_history[:-1] # omit current
                history_lines = []
                for msg in prior_messages:
                    speaker = "User" if msg.role == "user" else "Aibou"
                    history_lines.append(f"{speaker}: {msg.content}")

                # Retrieve RAG context
                injected_context = await get_rag_context(display_content, n_results=5)

                system_parts = [CORE_PROMPT, TOOL_DIRECTIVE]
                if history_lines:
                    system_parts.append("CONVERSATION HISTORY:\n" + "\n\n".join(history_lines))
                if injected_context:
                    system_parts.append("RECALLED MEMORIES & RELEVANT DOCUMENTS:\n" + injected_context)

                # Format attached documents and images directly into prompt context
                attached_doc_block = ""
                image_attachments = []
                if attachments:
                    doc_texts = []
                    for att in attachments:
                        if att.get("file_type") == "image" and att.get("image_url"):
                            image_attachments.append(att)
                        else:
                            fname = att.get("filename", "Uploaded File")
                            ftext = att.get("text", "")
                            if ftext:
                                doc_texts.append(f"📄 [ATTACHED DOCUMENT: {fname}]\n\"\"\"\n{ftext}\n\"\"\"")
                    if doc_texts:
                        attached_doc_block = "\n\n".join(doc_texts)

                user_instruction = content.strip() if content and content.strip() else ("Please analyze the attached image." if image_attachments else "Please read and analyze the attached document.")
                if attached_doc_block:
                    full_human_prompt = f"{attached_doc_block}\n\nUser Request: {user_instruction}"
                else:
                    full_human_prompt = user_instruction

                if image_attachments:
                    human_content: Any = [{"type": "text", "text": full_human_prompt}]
                    for img in image_attachments:
                        human_content.append({
                            "type": "image_url",
                            "image_url": {"url": img["image_url"]}
                        })
                    prompt_messages = [
                        SystemMessage(content="\n\n---\n\n".join(system_parts)),
                        HumanMessage(content=human_content)
                    ]
                else:
                    prompt_messages = [
                        SystemMessage(content="\n\n---\n\n".join(system_parts)),
                        HumanMessage(content=full_human_prompt)
                    ]


                # Dynamic provider selection: local Ollama vs OpenRouter cloud API
                if settings.USE_LOCAL_LLM or not settings.OPENROUTER_API_KEY:
                    base_llm = ChatOpenAI(
                        model=settings.MODEL_CHAT,
                        base_url=f"{settings.LOCAL_LLM_URL}/v1",
                        api_key=settings.LOCAL_LLM_API_KEY,
                        streaming=True,
                        temperature=0.75,
                        extra_body={"keep_alive": "15m"}
                    )
                else:
                    base_llm = ChatOpenAI(
                        model=settings.MODEL_CHAT,
                        base_url="https://openrouter.ai/api/v1",
                        api_key=settings.OPENROUTER_API_KEY,
                        streaming=True,
                        temperature=0.75,
                    )


                try:
                    llm = base_llm.bind_tools(aibou_tools)
                except Exception:
                    llm = base_llm

                accumulated_tokens = []
                
                await manager.send_personal_message({
                    "type": "status",
                    "node": "Aibou",
                    "conversation_id": current_chat.id,
                    "local_chat_id": local_chat_id
                }, user_id)

                try:
                    full_chunk = None
                    tool_calls_detected = False

                    try:
                        stream_target = llm.astream(prompt_messages)
                        async for chunk in stream_target:
                            if full_chunk is None:
                                full_chunk = chunk
                            else:
                                full_chunk += chunk

                            if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                                tool_calls_detected = True

                            delta = chunk.content if isinstance(chunk.content, str) else ""
                            if delta and not tool_calls_detected:
                                accumulated_tokens.append(delta)
                                await manager.send_personal_message({
                                    "type": "token",
                                    "delta": delta,
                                    "node": "Aibou",
                                    "conversation_id": current_chat.id,
                                    "local_chat_id": local_chat_id
                                }, user_id)
                    except Exception as stream_err:
                        # Fallback if model doesn't support tool schema
                        if "does not support tools" in str(stream_err) or "tools" in str(stream_err).lower():
                            async for chunk in base_llm.astream(prompt_messages):
                                delta = chunk.content if isinstance(chunk.content, str) else ""
                                if delta:
                                    accumulated_tokens.append(delta)
                                    await manager.send_personal_message({
                                        "type": "token",
                                        "delta": delta,
                                        "node": "Aibou",
                                        "conversation_id": current_chat.id,
                                        "local_chat_id": local_chat_id
                                    }, user_id)
                        else:
                            raise stream_err

                    # If model requested tool calls, run them locally and stream the answer
                    if full_chunk and hasattr(full_chunk, "tool_calls") and full_chunk.tool_calls:
                        prompt_messages.append(full_chunk)
                        
                        for tool_call in full_chunk.tool_calls:
                            t_name = tool_call.get("name")
                            t_args = tool_call.get("args", {})
                            t_id = tool_call.get("id", "call_1")

                            
                            await manager.send_personal_message({
                                "type": "tool_status",
                                "tool": t_name,
                                "status": "running",
                                "conversation_id": current_chat.id,
                                "local_chat_id": local_chat_id
                            }, user_id)
                            
                            tool_fn = tool_map.get(t_name)
                            if tool_fn:
                                try:
                                    if asyncio.iscoroutinefunction(tool_fn.func):
                                        tool_result = await asyncio.wait_for(tool_fn.func(**t_args), timeout=8.0)
                                    else:
                                        tool_result = await asyncio.wait_for(asyncio.to_thread(tool_fn.func, **t_args), timeout=8.0)
                                except Exception as err:
                                    tool_result = f"Error executing tool: {err}"
                            else:
                                tool_result = f"Tool {t_name} not found."

                            prompt_messages.append(ToolMessage(content=str(tool_result), tool_call_id=t_id))
                            
                            await manager.send_personal_message({
                                "type": "tool_status",
                                "tool": t_name,
                                "status": "done",
                                "conversation_id": current_chat.id,
                                "local_chat_id": local_chat_id
                            }, user_id)

                        # Stream synthesized response after tool execution using base_llm
                        async for chunk in base_llm.astream(prompt_messages):
                            delta = chunk.content if isinstance(chunk.content, str) else ""
                            if delta:
                                accumulated_tokens.append(delta)
                                await manager.send_personal_message({
                                    "type": "token",
                                    "delta": delta,
                                    "node": "Aibou",
                                    "conversation_id": current_chat.id,
                                    "local_chat_id": local_chat_id
                                }, user_id)



                except Exception as e:
                    await db.rollback()
                    err_text = str(e)
                    print(f"[WS CHAT ERROR] Generation failed: {err_text}")

                    if "not found" in err_text.lower() or "404" in err_text:
                        friendly_error = (
                            f"Model '{settings.MODEL_CHAT}' is not installed in your Ollama library yet. "
                            f"Run `ollama pull {settings.MODEL_CHAT}` in your terminal, or click the settings pill in the bottom-left to select an installed model."
                        )
                    else:
                        friendly_error = f"Generation error: {err_text}"

                    await manager.send_personal_message({
                        "type": "error",
                        "message": friendly_error,
                        "conversation_id": current_chat.id,
                        "local_chat_id": local_chat_id
                    }, user_id)
                    continue


                full_message = "".join(accumulated_tokens).strip()
                if "<think>" in full_message:
                    full_message = re.sub(r'<think>.*?</think>', '', full_message, flags=re.DOTALL).strip()

                if not full_message:
                    full_message = "I'm here. What's on your mind?"

                # Save AI response to DB
                ai_msg = Message(conversation_id=current_chat.id, role="assistant", content=full_message)
                db.add(ai_msg)

                generated_title: str | None = None
                if is_new_conversation:
                    generated_title = await generate_conversation_title(display_content)
                    current_chat.title = generated_title

                await db.commit()

                # Send completion confirmation
                await manager.send_personal_message({
                    "type": "complete",
                    "conversation_id": current_chat.id,
                    "local_chat_id": local_chat_id,
                    "message": full_message,
                    "title": generated_title,
                    "agent_path": "Aibou"
                }, user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"[WEBSOCKET] User {user_id} disconnected.")