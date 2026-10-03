from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.routers import materials

import uvicorn

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION,
    description="Микросервис для получения данных с папки на яндекс диске",
    docs_url="/docs",
    redoc_utl = "/redoc",
)

app.include_router(materials.router)

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    excluded_handlers=["/metrics", "/health"]
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])

@app.get("/health", tags=["Health"])
async def health_check():
    '''Эндпоинт для проверки жива ли служба'''
    return {"status": "ok", "service": settings.PROJECT_NAME}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
