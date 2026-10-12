from fastapi import HTTPException, status
import httpx

from src.config import settings


async def get_materials(
    public_key: str, path: str = "/", limit: int = 100, offset: int = 0
) -> dict:
    params = {
        "public_key": public_key or settings.YANDEX_DISK_PUBLIC_KEY,
        "path": path,
        "limit": limit,
        "offset": offset,
    }

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        try:
            response = await client.get(settings.YANDEX_DISK_API, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка сети при обращении к яндекс диску: {str(exc)}",
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Папка не найдена или нет доступа",
        )
    elif response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка яндекс диска api",
        )

    data = await response.json()
    items = []

    embedded = data.get("_embedded", {})
    raw_items = embedded.get("items", [])
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

    total_items = embedded.get("total", len(items))

    return {
        "status": "Успешно",
        "folder_info": {
            "name": data.get("name", "Root"),
            "path": data.get("path", "/"),
            "total_items": total_items,
        },
        "items": items,
    }
