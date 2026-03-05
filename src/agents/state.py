from typing import Annotated, TypedDict, Sequence, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.core.config import settings


_summarizer_llm = None

def _get_summarizer():
    """Lazy init so the LLM client isn't created at import time."""
    global _summarizer_llm
    if _summarizer_llm is None:
        _summarizer_llm = ChatOpenAI(
            model=settings.MODEL_CHAT,
            base_url=f"{settings.LOCAL_LLM_URL}/v1",
            api_key=settings.LOCAL_LLM_API_KEY,
            temperature=0.1
        )
    return _summarizer_llm

def compress_memory_window(existing_messages: Sequence[BaseMessage], new_messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    total_messages = list(existing_messages) + list(new_messages)
    
    if len(total_messages) > 15:
        system_prompt = total_messages[0]
        
        messages_to_compress = total_messages[1:7]
        recent_messages = total_messages[7:]
        
        raw_log = "\n".join([
            f"{msg.type.upper()}: {msg.content}" for msg in messages_to_compress
        ])
        
        prompt = f"""Summarize the following conversation log into a concise 2-3 sentence technical summary. 
        Focus strictly on what the user wants, any architectural decisions made, and what code was discussed. 
        Do not add conversational filler.
    
        LOG:
        {raw_log}"""
        
        try:
            summary_response = _get_summarizer().invoke(prompt)
            summary_text = summary_response.content.strip()
        except Exception as e:
            print(f"[WARNING] Summarizer LLM failed: {e}")
            summary_text = f"Archived {len(messages_to_compress)} previous messages."
        
        archive_message = SystemMessage(
            content=f"--- ARCHIVED CONVERSATION CONTEXT ---\nSummary of previous events:\n{summary_text}\n--- END ARCHIVED CONTEXT ---"
        )
        
        return [system_prompt, archive_message] + recent_messages
        
    return total_messages


def update_artifacts(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    if existing is None:
        existing = {}
    if new is None:
        return existing
        
    updated = existing.copy()
    updated.update(new)
    return updated


class AibouState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], compress_memory_window]
    
    artifacts: Annotated[Dict[str, Any], update_artifacts]
    
    current_agent: str
    
    current_code: str
    
    execution_output: str
    
    retry_count: int
    
    requires_human_approval: bool