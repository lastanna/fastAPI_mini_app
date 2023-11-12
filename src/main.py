import uvicorn
from fastapi import FastAPI
from src.api.my_mini_service import router as my_mini_service_router
from src.api.events import router as events_router
from src.core.config import app_settings

app = FastAPI(
    title=app_settings.app_title,  # зададим название сервиса для вывода в swagger
    docs_url='/api/swagger-ui'  # зададим префикс вместо /docs
)

app.include_router(my_mini_service_router)  # эндпоинты
app.include_router(events_router)  # запуск и остановка сервиса

if __name__ == '__main__':
    uvicorn.run(
        app,
        host=app_settings.project_host,
        port=app_settings.project_port
    )
