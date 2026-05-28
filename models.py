import hashlib
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///finance.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Связь с транзакциями
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля методом SHA-256 для защиты данных в БД"""
        return hashlib.sha256(password.encode()).hexdigest()

    # ВОТ ЭТОТ МЕТОД МЫ ДОБАВЛЯЕМ СЕЙЧАС:
    def verify_password(self, password: str) -> bool:
        """Проверка соответствия введённого пароля хешу из базы данных"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


class Transaction(Base):
    __tablename__ = 'transactions'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Новое поле: тип операции ("income" или "expense")
    type = Column(String, nullable=False, default="expense")

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Обратная связь с пользователем
    user = relationship("User", back_populates="transactions")


# Функция для автоматического создания таблиц при старте (которую мы потеряли вчера)
def init_db():
    Base.metadata.create_all(bind=engine)