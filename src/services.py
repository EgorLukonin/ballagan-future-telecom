from fastapi import HTTPException, status
import httpx

from src.config import settings
from src.app_logging import get_logger

logger = get_logger(__name__)


async def get_materials(
    public_key: str, path: str = "/", limit: int = 100, offset: int = 0
) -> dict:
    params = {
        "public_key": public_key or settings.YANDEX_DISK_PUBLIC_KEY,
        "path": path,
        "limit": limit,
        "offset": offset,
    }

    masked_key = public_key[:30] + "***" if len(public_key) > 30 else "***"
    logger.info(
        "Fetching materials from Yandex Disk",
        yandex_disk_key=masked_key,
        path=path,
        limit=limit,
        offset=offset,
    )

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        try:
            response = await client.get(settings.YANDEX_DISK_API, params=params)
        except httpx.RequestError as exc:
            logger.error(
                "Network error calling Yandex Disk API",
                error=str(exc),
                yandex_disk_key=masked_key,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ошибка сети при обращении к яндекс диску: {str(exc)}",
            )

    if response.status_code == 404:
        logger.warning(
            "Yandex Disk folder not found or no access",
            yandex_disk_key=masked_key,
            status_code=404,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Папка не найдена или нет доступа",
        )
    elif response.status_code != 200:
        logger.error(
            "Yandex Disk API returned error",
            yandex_disk_key=masked_key,
            status_code=response.status_code,
            response_text=response.text[:500],
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка яндекс диска api",
        )

    data = response.json()
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

    logger.info(
        "Successfully fetched materials from Yandex Disk",
        yandex_disk_key=masked_key,
        total_items=total_items,
        returned_items=len(items),
    )

    return {
        "status": "Успешно",
        "folder_info": {
            "name": data.get("name", "Root"),
            "path": data.get("path", "/"),
            "total_items": total_items,
        },
        "items": items,
    }
