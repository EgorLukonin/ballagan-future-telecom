from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException
import httpx

from src.services import get_materials


@pytest.mark.asyncio
@patch("src.services.httpx.AsyncClient")
async def test_get_materials_success(mock_async_client_cls):
    """Тест успешного получения материалов через сервис get_materials."""
    # Создаем мок для ответа от httpx
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "RootFolder",
        "path": "/",
        "_embedded": {
            "total": 1,
            "items": [
                {
                    "name": "lection.pdf",
                    "type": "file",
                    "size": 2048,
                    "mime_type": "application/pdf",
                    "file": "https://downloader.disk.yandex.ru/test_file",
                }
            ],
        },
    }

    # Настраиваем поведение AsyncClient в виде контекстного менеджера
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    result = await get_materials(
        public_key="https://disk.yandex.ru/d/test_key",
        path="/",
        limit=10,
        offset=0,
    )

    assert result["status"] == "Успешно"
    assert result["folder_info"]["name"] == "RootFolder"
    assert result["folder_info"]["total_items"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "lection.pdf"
    assert result["items"][0]["size"] == 2048


@pytest.mark.asyncio
@patch("src.services.httpx.AsyncClient")
async def test_get_materials_not_found(mock_async_client_cls):
    """Тест обработки статуса 404 (папка не найдена или нет доступа)."""
    mock_response = AsyncMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        await get_materials(public_key="https://disk.yandex.ru/d/invalid_key")

    assert exc_info.value.status_code == 404
    assert "не найдена" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@patch("src.services.httpx.AsyncClient")
async def test_get_materials_bad_request(mock_async_client_cls):
    """Тест обработки непредвиденных статус-кодов API Яндекс Диска (например, 500)."""
    mock_response = AsyncMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        await get_materials(public_key="https://disk.yandex.ru/d/test_key")

    assert exc_info.value.status_code == 400
    assert "ошибка" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@patch("src.services.httpx.AsyncClient")
async def test_get_materials_network_error(mock_async_client_cls):
    """Тест обработки сетевой ошибки (httpx.RequestError -> 503)."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.RequestError("Network is unreachable")
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client

    with pytest.raises(HTTPException) as exc_info:
        await get_materials(public_key="https://disk.yandex.ru/d/test_key")

    assert exc_info.value.status_code == 503
    assert "ошибка сети" in exc_info.value.detail.lower()
