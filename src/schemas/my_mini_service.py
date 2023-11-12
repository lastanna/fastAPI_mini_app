from pydantic import BaseModel, Field
import uuid

# schemas для валидации полученных данных
class Address(BaseModel):
    address: str


class ContactUpdate(BaseModel):
    phone: str
    address: str


class ContactCreate(ContactUpdate):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


if __name__ == '__main__':
    # проверка генерации uuid
    print(ContactCreate(phone='+7(928)4343437', address='test'))
