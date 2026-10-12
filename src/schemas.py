from pydantic import BaseModel


class MaterialItem(BaseModel):
    name: str
    type: str
    size: int = 0
    mime_type: str | None
    file: str | None


class FolderInfo(BaseModel):
    name: str
    path: str
    total_items: int


class MaterialListResponse(BaseModel):
    status: str
    folder_info: FolderInfo
    items: list[MaterialItem]


class ErrorResponse(BaseModel):
    status: str
    error_code: str
    message: str
