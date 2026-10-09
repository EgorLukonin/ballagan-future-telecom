from unittest.mock import AsyncMock, patch


@patch("src.routers.materials.settings")
@patch("src.routers.materials.get_materials", new_callable=AsyncMock)
def test_missing_header_uses_default_key(mock_get_materials, mock_settings, client):
    """Проверка: если заголовок отсутствует, берется ключ по умолчанию из settings"""
    mock_settings.YANDEX_DISK_PUBLIC_KEY = "https://disk.yandex.ru/d/test_default_key"

    mock_get_materials.return_value = {
        "status": "Успешно",
        "folder_info": {
            "name": "Тестовая папка",
            "path": "/",
            "total_items": 0,
        },
        "items": [],
    }

    response = client.get("/api/v1/materials/list")

    assert response.status_code == 200
    mock_get_materials.assert_called_once()


def test_invalid_header_prefix_returns_401(client):
    """Проверка валидации формата ссылки в заголовке"""
    headers = {"X-Disk-Folder-Link": "https://google.com"}
    response = client.get("/api/v1/materials/list", headers=headers)

    assert response.status_code == 401
    assert "некорректна" in response.json()["detail"].lower()


@patch("src.routers.materials.get_materials", new_callable=AsyncMock)
def test_get_materials_success(mock_get_materials, client):
    """Тест успешного ответа"""
    mock_get_materials.return_value = {
        "status": "Успешно",
        "folder_info": {
            "name": "Тестовая папка",
            "path": "/",
            "total_items": 1,
        },
        "items": [
            {
                "name": "test.txt",
                "type": "file",
                "size_bytes": 128,
                "mime_type": "text/plain",
                "download_url": "https://downloader.disk.yandex.ru/test",
            }
        ],
    }

    headers = {"X-Disk-Folder-Link": "https://disk.yandex.ru/d/test_key"}
    response = client.get("/api/v1/materials/list", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Успешно"
    assert data["folder_info"]["total_items"] == 1
    assert data["items"][0]["name"] == "test.txt"

    mock_get_materials.assert_called_once_with(
        public_key="https://disk.yandex.ru/d/test_key",
        path="/",
    )
