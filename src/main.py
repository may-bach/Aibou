from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message, MemoryFact


app = FastAPI(title="Aibou API")

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None


@app.post("/users/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )
    

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"message": "User created successfully!", "user": new_user.username, "id": new_user.id}