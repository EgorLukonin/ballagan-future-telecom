from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException, Query, status

from src.config import settings
from src.schemas import ErrorResponse, MaterialListResponse
from src.services import get_materials

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


@router.get(
    "/list",
    response_model=MaterialListResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def get_materials_list(
    x_disk_folder_link: Optional[str] = Header(
        None,
        alias="X-Disk-Folder-Link",
        description="Ссылка на папку на Яндекс Диске",
    ),
    path: str = Query("/", description="Путь к подпапке"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит элементов"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
):
    target_link = x_disk_folder_link or settings.YANDEX_DISK_PUBLIC_KEY

    # Безопасная проверка домена через urlparse
    parsed_url = urlparse(target_link)
    allowed_netlocs = {"disk.yandex.ru", "disk.yandex.com", "yadi.sk"}

    if parsed_url.scheme != "https" or parsed_url.netloc not in allowed_netlocs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректная ссылка на Яндекс Диск.",
        )
    result = await get_materials(
        public_key=target_link, path=path, limit=limit, offset=offset
    )
    return result
