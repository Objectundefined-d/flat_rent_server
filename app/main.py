from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import threading
from .api import photos
from .core.config import settings
from .core.firebase import init_firebase, start_matches_listener
from .core.firebase import init_firebase, start_matches_listener, start_messages_listener

app = FastAPI(
    title="Photo Storage API",
    description="Сервер для хранения фото",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(photos.router)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

@app.on_event("startup")
async def startup_event():
    init_firebase()
    threading.Thread(target=start_matches_listener, daemon=True).start()
    threading.Thread(target=start_messages_listener, daemon=True).start()

@app.get("/")
async def root():
    return {
        "message": "Photo Storage API",
        "docs": "/docs",
        "health": "/api/photos/health"
    }