import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routers import users, chat, voice, config
from src.db.session import engine
from src.services.gpu_watchdog import start_gpu_game_watchdog
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.db.session import init_database
    await init_database()

    # Start GPU game watchdog
    watchdog_task = asyncio.create_task(start_gpu_game_watchdog())

    yield

    watchdog_task.cancel()
    print("Aibou API is shutting down...")

app = FastAPI(title="Aibou API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


app.include_router(users.router)
app.include_router(chat.router)
app.include_router(voice.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")