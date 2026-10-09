from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query

from src.config import settings
from src.schemas import Error_Response
from src.services import get_materials

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


@router.get(
    "/list",
    responses={
        401: {"model": Error_Response},
        404: {"model": Error_Response},
        503: {"model": Error_Response},
    },
)
async def get_materials_list(
    x_disk_folder_link: Optional[str] = Header(
        None,
        alias="X-Disk-Folder-Link",
        description="Ссылка на папку на Яндекс Диске",
    ),
    path: str = Query("/", description="Путь к подпапке"),
):
    target_link = x_disk_folder_link or settings.YANDEX_DISK_PUBLIC_KEY

    if not target_link or not target_link.startswith("https://disk.yandex"):
        raise HTTPException(
            status_code=401,
            detail="Не указана или некорректна ссылка на папку Яндекс Диска.",
        )

    result = await get_materials(public_key=target_link, path=path)
    return result
