import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
from ..core.config import settings

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = 1200  # максимальная ширина/высота
COMPRESS_QUALITY = 85  # качество сжатия (0-100)

async def save_upload_file(upload_file: UploadFile, user_id: str) -> dict:
    """Сохраняет загруженный файл и возвращает информацию о нем"""
    
    # Проверяем расширение
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Неподдерживаемый формат. Разрешены: {ALLOWED_EXTENSIONS}")
    
    # Создаем папку пользователя
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    new_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(user_dir, new_filename)
    
    # Читаем содержимое файла
    contents = await upload_file.read()
    
    # Проверяем размер
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(400, f"Файл слишком большой. Максимум {settings.MAX_FILE_SIZE/1024/1024}MB")
    
    # Сжимаем изображение
    compressed_contents = compress_image(contents, file_ext)
    
    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(compressed_contents)
    
    # Формируем URL для доступа к файлу
    file_url = f"/files/{user_id}/{new_filename}"
    
    return {
        "file_name": new_filename,
        "file_url": file_url,
        "file_size": len(compressed_contents),
        "original_name": upload_file.filename
    }

def compress_image(image_bytes: bytes, file_ext: str) -> bytes:
    """Сжимает изображение"""
    try:
        # Открываем изображение
        img = Image.open(io.BytesIO(image_bytes))
        
        # Конвертируем в RGB если нужно (для PNG с альфа-каналом)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Уменьшаем размер если слишком большое
        if max(img.size) > MAX_IMAGE_SIZE:
            ratio = MAX_IMAGE_SIZE / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Сохраняем в JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=COMPRESS_QUALITY, optimize=True)
        
        return output.getvalue()
    
    except Exception as e:
        # Если не удалось сжать, возвращаем оригинал
        return image_bytes

async def delete_file(file_path: str):
    """Удаляет файл"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except:
        pass
    return False

def get_file_path(user_id: str, file_name: str) -> str:
    """Возвращает полный путь к файлу"""
    return os.path.join(settings.UPLOAD_DIR, user_id, file_name)