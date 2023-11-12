import logging
import logging.config
from fastapi import APIRouter
from src.db.db import engine, Base
from src.core.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger()

router = APIRouter()


@router.on_event("startup")
async def init_tables():
    """
    При запуске приложения
    """
    async with engine.begin() as conn:
        # если нужно удалить все таблицы из бд запускаем закомментированную строку
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@router.on_event('shutdown')
async def shutdown():
    """
    Выход из контекста и сбор мусора (object is gabage collected)
    """
    await engine.dispose()
