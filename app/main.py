from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .api import photos
from .core.config import settings

# Создаем приложение
app = FastAPI(
    title="Photo Storage API",
    description="Сервер для хранения фото",
    version="1.0.0"
)

# Настраиваем CORS для Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничьте
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(photos.router)

# Раздаем статические файлы
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

@app.get("/")
async def root():
    return {
        "message": "Photo Storage API",
        "docs": "/docs",
        "health": "/api/photos/health"
    }