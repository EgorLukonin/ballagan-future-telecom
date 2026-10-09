from fastapi import HTTPException, status
import httpx

from src.config import settings


async def get_materials(public_key: str, path: str = "/") -> dict:
    params = {
        "public_key": public_key or settings.YANDEX_DISK_PUBLIC_KEY,
        "path": path,
        "limit": 100,
    }

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        try:
            response = await client.get(settings.YANDEX_DISK_API, params=params)
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервис Яндекс Диска временно недоступен.",
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс или папка на Яндекс Диске не найдены.",
        )
    elif response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ошибка при получении данных с Яндекс Диска.",
        )

    data = response.json()
    items = []

    raw_items = data.get("_embedded", {}).get("items", [])
    for item in raw_items:
        items.append(
            {
                "name": item.get("name"),
                "type": item.get("type"),
                "size": item.get("size", 0),
                "mime_type": item.get("mime_type"),
                "file": item.get("file"),
            }
        )

    return {
        "status": "Успешно",
        "folder_info": {
            "name": data.get("name", "Root"),
            "path": data.get("path", "/"),
            "total_items": len(items),
        },
        "items": items,
    }
