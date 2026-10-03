from pydantic import BaseModel

class Material_Item(BaseModel):
    name: str 
    type: str 
    size_bytes: int = 0
    mime_type: str | None
    download_url: str | None

class Folder_Info(BaseModel):
    name: str
    path: str
    total_items: int

class Material_List_Response(BaseModel):
    status: str
    folder_info: Folder_Info
    items: list[Material_Item]

class Error_Response(BaseModel):
    status: str
    error_code: str
    message: str
