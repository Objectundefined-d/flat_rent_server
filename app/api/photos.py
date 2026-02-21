from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
from ..core.security import verify_token
from ..utils.file_handler import save_upload_file, delete_file, get_file_path
from ..core.config import settings

router = APIRouter(prefix="/api/photos", tags=["photos"])

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    """Загрузка фото"""
    try:
        result = await save_upload_file(file, user["user_id"])
        return {
            "success": True,
            "data": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, f"Ошибка загрузки: {str(e)}")

@router.get("/files/{user_id}/{file_name}")
async def get_file(user_id: str, file_name: str):
    """Получение файла"""
    file_path = get_file_path(user_id, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "Файл не найден")
    
    return FileResponse(file_path)

@router.delete("/files/{file_name}")
async def delete_photo(
    file_name: str,
    user: dict = Depends(verify_token)
):
    """Удаление фото"""
    file_path = get_file_path(user["user_id"], file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "Файл не найден")
    
    deleted = await delete_file(file_path)
    
    if deleted:
        return {"success": True, "message": "Файл удален"}
    else:
        raise HTTPException(500, "Ошибка удаления")

@router.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "ok",
        "upload_dir": settings.UPLOAD_DIR,
        "max_file_size": settings.MAX_FILE_SIZE
    }