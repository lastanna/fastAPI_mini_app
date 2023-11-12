import logging
import logging.config

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import app_settings
from src.core.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger()

Base = declarative_base()
# подключаемся к базе данных
# echo true позволяет при запуске движка увидеть сгенерированные sql запросы
engine = create_async_engine(
        app_settings.database_dsn,
        echo=True,
    )
# sessionmaker - фабрика для создания асинхронной сессии
# для каждого запроса создается своя сессия
# expire_on_commit - завершается ли сессия после коммита
async_session = sessionmaker(engine, class_=AsyncSession,
                             expire_on_commit=False)

# Функция понадобится при внедрении зависимостей
# Асинхронный менеджер контекста, генератор сессии
async def get_session() -> AsyncSession:
    async with async_session() as session:
        logger.info('session is being started...')
        yield session
