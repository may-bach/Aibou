from fastapi import FastAPI
from src.api.routers import users, chat

app = FastAPI(title="Aibou API")

app.include_router(users.router)
app.include_router(chat.router)