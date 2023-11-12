import aioredis
import logging
import logging.config
import phonenumbers
from typing import Tuple, Dict

from asyncpg.exceptions._base import InterfaceError, PostgresError

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text


from src.schemas.my_mini_service import Address, ContactCreate
from src.schemas.my_mini_service import ContactUpdate
from src.models.my_mini_service import Contacts as ContactModel
from src.db.db import get_session
from src.core.config import app_settings
from src.core.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)
router = APIRouter()
router.include_router(router, prefix='/my_mini_service',
                      tags=['my_mini_service'])

# создаем асинхронное соединение с редис
redis = aioredis.from_url(
    app_settings.redis_dsn,
    encoding='utf-8',
    decode_responses=True)

logger.info('Redis is connected...')

# буду использовать редис как очередь: добавляю в конец, удаляю сначала.


async def validate_phone(phone):
    """
    Проверяет соответствуют ли введенный данные паттерну телефоного номера
    """
    symbols = (' ', '(', ')', '-')
    cleaned_phone = phone.strip()
    for symbol in symbols:
        cleaned_phone = cleaned_phone.replace(symbol, '')
    try:
        phonenumbers.is_valid_number(phonenumbers.parse(cleaned_phone))
    except phonenumbers.phonenumberutil.NumberParseException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Invalid phone number')
    return cleaned_phone


async def get_contact_or_404(
        phone: str,
        db: AsyncSession = Depends(get_session)
) -> Address:
    """

    :param phone: телефонный номер в любом формате
    :param db: сессия асинхронного соединения с бд
    :return: Schema Адреса
    """
    statement = select(ContactModel).where(ContactModel.phone == phone)
    results = await db.execute(statement)
    if results is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Address not found')
    return results.scalar_one_or_none()


@router.get("/ping")
async def ping(db: AsyncSession = Depends(get_session)) -> Dict:
    """
    Возвращает информацию о статусе доступности БД
    """
    try:
        await db.execute(text("SELECT 1"))
        logger.info('The database is connected')
        return {"status": "pong", "msg": "The database is connected"}
    except InterfaceError:
        return {"status": "Cannot connect to a database"}


@router.get('/check_data', response_model=Address)
async def check_data(
        phone: str = Depends(validate_phone),
        db: AsyncSession = Depends(get_session)
) -> Tuple[Address, str]:
    """
    Проверяет адрес по номеру телефона
    :param phone: номер телефона, валидируется через функцию передаваемую через
    Dependency Injection, возвращается без лишних символов (+ и одинадцать цифр)
    :param db: ассинхронная сессия бд
    :return: адрес из бд, адрес из редис
    """
    address_from_redis = await redis.lpop(phone)
    # проверяем, есть ли такой номер в бд, возвращаем сооответствующую запись
    entry = await get_contact_or_404(phone, db)
    address = Address(address=entry.address)
    return address, address_from_redis


@router.post('/write_data', status_code=status.HTTP_201_CREATED)
async def write_data(address: str,
                     phone: str = Depends(validate_phone),
                     db: AsyncSession = Depends(get_session)):
    """
    Создает новую запись, добавляет в редис и бд
    :param address: адрес
    :param phone: номер телефона, валидируется через функцию передаваемую через
    Dependency Injection, возвращается без лишних символов (+ и одинадцать цифр)
    :param db: ассинхронная сессия бд
    :return: добавленную запись бд
    """
    await redis.rpush(phone, address)
    # Проверяем есть ли такой телефон в бд, если есть, то возвращаем BAD_REQUEST
    entry = await get_contact_or_404(phone, db)
    if not entry:
        contact = ContactCreate(phone=phone, address=address)
        contact_dump = contact.model_dump()
        statement = insert(ContactModel).values(contact_dump)
        try:
            await db.execute(statement=statement)
            await db.commit()
            logger.info(f'New entry {entry} is added into the database')
        except PostgresError as e:
            logger.error(f'Database error {e}')
        contact_db = await get_contact_or_404(phone, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='The phone that you\'ve entered is already in database'
        )
    return contact_db


@router.patch('/write_data', status_code=status.HTTP_200_OK)
async def update_data(address: str,
                      phone: str = Depends(validate_phone),
                      db: AsyncSession = Depends(get_session)
                      ) -> ContactUpdate:
    """
    Меняет адрес по телефону в редис и бд
    :param address: адрес
    :param phone: номер телефона, валидируется через функцию передаваемую через
    Dependency Injection, возвращается без лишних символов (+ и одинадцать цифр)
    :param db: ассинхронная сессия бд
    :return: добавленную запись бд
    """
    await redis.rpush(phone, address)
    # Проверяем есть ли такой телефон в бд
    contact_db = await get_contact_or_404(phone, db)
    if contact_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Phone not found, if you want to create a new contact, use POST')
    statement = update(ContactModel).where(
        ContactModel.phone==contact_db.phone
    ).values(address=address)
    await redis.rpush(phone, address)
    try:
        await db.execute(statement=statement)
        await db.commit()
        logger.info(f'Address for {phone} has been updated')
    except PostgresError as e:
        logger.error(f'Database error {e}')
    contact = ContactUpdate(phone=phone, address=address)
    return contact
