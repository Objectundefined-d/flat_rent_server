import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime
from .config import settings

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Проверяет Firebase JWT токен"""
    token = credentials.credentials
    
    try:
        # Для Firebase токенов используйте библиотеку firebase-admin
        # Здесь простая заглушка - в реальности проверяйте токен
        
        # Просто декодируем (не проверяя подпись) чтобы получить user_id
        # В продакшене используйте firebase-admin
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Извлекаем user_id из токена
        user_id = payload.get("user_id") or payload.get("sub") or payload.get("uid")
        
        if not user_id:
            raise HTTPException(401, "Нет user_id в токене")
        
        return {"user_id": user_id, "token": token}
    
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Неверный токен")
    except Exception as e:
        raise HTTPException(401, f"Ошибка авторизации: {str(e)}")