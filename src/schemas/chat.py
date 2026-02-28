from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: int
    content: str
    conversation_id: int | None = None