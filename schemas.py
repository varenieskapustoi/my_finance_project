from pydantic import BaseModel
from datetime import datetime

# ==================== СХЕМЫ ДЛЯ ТРАНЗАКЦИЙ ====================

# Базовая схема: что мы обязательно ждем от фронтенда при создании/редактировании
class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: str | None = None

# Полная схема: что мы отдаем обратно (уже содержит ID и дату из базы)
class Transaction(TransactionCreate):
    id: int
    created_at: datetime

    class Config:
        # Позволяет Pydantic автоматически читать данные из объектов SQLAlchemy (ORM)
        from_attributes = True


# ==================== СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ====================

# Схема для получения данных при регистрации/входе
class UserCreate(BaseModel):
    username: str
    password: str

# Схема для отдачи данных пользователя наружу (без пароля!)
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        # Позволяет Pydantic автоматически читать данные из объектов SQLAlchemy (ORM)
        from_attributes = True