from fastapi import APIRouter, Header, Query, HTTPException, status
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
    x_disk_folder_link: str = Header(
        ..., alias="X-Disk-Folder-Link", description="Ссылка на папку в яндекс диске"
    ),
    path: str = Query("/", description="Путь к подкапке"),
):
    if not x_disk_folder_link.startswith("https://disk.yandex"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Заголовок X-Disk-Folder-Link неверен. Укажите корреткную ссылку",
        )

    result = await get_materials(public_key=x_disk_folder_link, path=path)

    return result
