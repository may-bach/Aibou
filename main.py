from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routers import users, chat
from src.db.session import engine
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.include_router(users.router)
app.include_router(chat.router)