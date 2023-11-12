from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from src.db.db import Base

# модель для соответствующей таблицы в бд
class Contacts(Base):
    __tablename__ = 'contacts'

    id = Column(UUID(as_uuid=True), primary_key=True)
    phone = Column(String)
    address = Column(String)
