from typing import Optional
from fastapi import APIRouter, Header, Query, HTTPException, status
from src.config import settings
from src.schemas import Material_List_Response, Error_Response
from src.services import get_materials

router = APIRouter(prefix="/api/v1/materials", tags=["Materials"])

@router.get(
    "/list",
    response_model=Material_List_Response,
    responses={
        401: {"model": Error_Response},
        404: {"model": Error_Response},
        503: {"model": Error_Response},
    },
)
async def get_materials_list(
    x_disk_folder_link: Optional[str] = Header(
        None, alias="X-Disk-Folder-Link", description="Ссылка на папку на Яндекс Диске"
    ),
    path: str = Query("/", description="Путь к подпапке"),
):
    # Если заголовок не передан, берем дефолтный ключ из конфигурации 
    # (env / SealedSecrets)
    target_link = x_disk_folder_link or settings.YANDEX_DISK_PUBLIC_KEY

    if not target_link or not target_link.startswith("https://disk.yandex"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не указана или некорректна ссылка на папку Яндекс Диска.",
        )

    result = await get_materials(public_key=target_link, path=path)
    return result
