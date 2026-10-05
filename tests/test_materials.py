from unittest.mock import AsyncMock, patch


def test_missing_header_returns_422(client):
    """Проверка ошибки валидации при отсутствии заголовка"""
    response = client.get("/api/v1/materials/list")
    assert response.status_code == 422


def test_invalid_header_prefix_returns_401(client):
    """Проверка валидации формата ссылки в заголовке"""
    headers = {"X-Disk-Folder-Link": "https://google.com"}
    response = client.get("/api/v1/materials/list", headers=headers)

    assert response.status_code == 401
    assert "X-Disk-Folder-Link" in response.json()["detail"]


@patch("src.routers.materials.get_materials", new_callable=AsyncMock)
def test_get_materials_success(mock_get_materials, client):
    """Тест успешного ответа"""
    # Задаем фейковый ответ, который вернет сервис
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

    # Проверяем, что сервисный метод вызван с правильными аргументами
    mock_get_materials.assert_called_once_with(
        public_key="https://disk.yandex.ru/d/test_key",
        path="/",
    )