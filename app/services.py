import httpx
from fastapi import HTTPException, status
from app.config import settings

YANDEX_API = "https://cloud-api.yandex.net/v1/disk/public/resources"

async def get_materials(publick_key: str, path: str = "/") -> dict:
    params = {
        "public_key": publick_key,
        "path": path,
        "limit": 100
    }

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        try:
            response = await client.get(settings.YANDEX_DISK_API, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=f"Ошибка сети при обращении к яндекс диску: {str(exc)}"
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Папка не найдена или нет доступа"
        )
    elif response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ошибка яндекс дикса api'
        )

    return response.json()