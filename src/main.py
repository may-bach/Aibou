from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from src.api import chat
from src.db.session import get_db
from src.models.user import User
from src.models.memory import Conversation, Message, MemoryFact


app = FastAPI(title="Aibou API")
app.include_router(chat.router)

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None

    class Config:
        from_attributes = True

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

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    # If the ID doesn't exist, throw a 404 Error
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Return the raw database object (Pydantic will automatically convert it to JSON)
    return user