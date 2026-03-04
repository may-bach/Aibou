from typing import Annotated, TypedDict, Sequence, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage


def compress_memory_window(existing_messages: Sequence[BaseMessage], new_messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    total_messages = list(existing_messages) + list(new_messages)
    
    if len(total_messages) > 15:
        system_prompt = total_messages[0]
        
        messages_to_compress = total_messages[1:7]
        
        recent_messages = total_messages[7:]
        compression_text = "\n".join([
            f"{msg.type.upper()}: {msg.content}" for msg in messages_to_compress
        ])
        
        #to keep the fastapi from crashing due to htting context window.
        archive_message = SystemMessage(
            content=f"--- ARCHIVED CONVERSATION CONTEXT ---\nThe following is a compressed log of the messages:\n{compression_text}\n--- END ARCHIVED CONTEXT ---"
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