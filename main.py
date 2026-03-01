from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routers import users, chat
from src.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing PostgreSQL Database...")
    async with engine.begin() as conn:
        from src.models.user import Base 
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

    yield

    print("Aibou API is shutting down...")

app = FastAPI(title="Aibou API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(chat.router)