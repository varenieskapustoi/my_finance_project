import datetime
import hashlib  # Добавили для защиты паролей
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # ВОТ ОНА — ПОЛНОЦЕННАЯ СВЯЗЬ SQLAlchemy:
    # Теперь у пользователя будет виртуальное поле .transactions, где лежат все его траты
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    # Метод для создания хэша пароля
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ИСПРАВЛЕНО: Добавили метод для проверки пароля при логине
    def verify_password(self, password: str) -> bool:
        """Сравнивает хэш введённого пароля с хэшем из базы данных"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Обратная связь: каждая транзакция знает, какому объекту User она принадлежит
    user = relationship("User", back_populates="transactions")


DATABASE_URL = 'sqlite:///finance.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("База данных и таблицы успешно инициализированы!")

if __name__ == "__main__":
    init_db()