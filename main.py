from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
import schemas

# --- ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ---
models.init_db()  # Инициализируем базу данных один раз

app = FastAPI(title="Finance App API", version="1.0.0")
templates = Jinja2Templates(directory="templates")


# Зависимость для управления сессиями БД
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- ЭНДПОИНТЫ ДЛЯ СТРАНИЦ (ФРОНТЕНД) ---

@app.get("/", response_class=HTMLResponse, tags=["Страницы"])
def read_root(request: Request):
    """Главная HTML-страницу веб-интерфейса"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login-page", response_class=HTMLResponse, tags=["Страницы"])
def get_login_page(request: Request):
    """Страница логина"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register-page", response_class=HTMLResponse, tags=["Страницы"])
def get_register_page(request: Request):
    """Страница регистрации (исправлено: больше не будет 404!)"""
    # Если файл формы называется index.html, замени ниже на "index.html"
    return templates.TemplateResponse("register.html", {"request": request})


# --- ЭНДПОИНТЫ ДЛЯ АНАЛИТИКИ И ТРАНЗАКЦИЙ ---

@app.get("/transactions/analytics", tags=["Транзакции"])
def get_analytics(request: Request, db: Session = Depends(get_db)):
    """Получить агрегированные данные по категориям строго для вошедшего юзера"""
    # Читаем куку авторизации
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")

    # Берем транзакции только этого пользователя
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == int(user_id)).all()

    analytics = {}
    for t in transactions:
        if t.category in analytics:
            analytics[t.category] += t.amount
        else:
            analytics[t.category] = t.amount

    return analytics


@app.get("/transactions", response_model=list[schemas.Transaction], tags=["Транзакции"])
def get_transactions(request: Request, db: Session = Depends(get_db)):
    """Получить список транзакций только текущего пользователя"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")

    # Фильтруем по user_id
    return db.query(models.Transaction).filter(models.Transaction.user_id == int(user_id)).all()


@app.post("/transactions", response_model=schemas.Transaction, tags=["Транзакции"])
def create_transaction(request: Request, item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """Добавить новую транзакцию (доход или расход) для вошедшего пользователя"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")

    new_item = models.Transaction(
        amount=item.amount,
        category=item.category,
        type=item.type,  # Подхватываем тип из фронтенда/схемы
        description=item.description,
        user_id=int(user_id)
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/transactions/balance", tags=["Транзакции"])
def get_balance(request: Request, db: Session = Depends(get_db)):
    """Посчитать общий баланс, сумму доходов и сумму расходов для текущего юзера"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")

    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == int(user_id)).all()

    total_income = 0.0
    total_expense = 0.0

    for t in transactions:
        if t.type == "income":
            total_income += t.amount
        else:
            total_expense += t.amount

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }


@app.get("/transactions", response_model=list[schemas.Transaction], tags=["Транзакции"])
def get_transactions(db: Session = Depends(get_db)):
    """Получить список всех транзакций"""
    return db.query(models.Transaction).all()


@app.post("/transactions", response_model=schemas.Transaction, tags=["Транзакции"])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """Добавить новую транзакцию"""
    new_item = models.Transaction(
        amount=item.amount,
        category=item.category,
        description=item.description,
        user_id=1  # Временная заглушка до привязки к кукам
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@app.put("/transactions/{transaction_id}", response_model=schemas.Transaction, tags=["Транзакции"])
def update_transaction(transaction_id: int, item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """Редактировать существующую транзакцию по её ID"""
    db_item = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    db_item.amount = item.amount
    db_item.category = item.category
    db_item.description = item.description

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/transactions/{transaction_id}", tags=["Транзакции"])
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Удалить транзакцию по её ID"""
    db_item = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    db.delete(db_item)
    db.commit()
    return {"status": "success", "message": f"Транзакция с ID {transaction_id} успешно удалена"}


# --- ЭНДПОИНТЫ АВТОРИЗАЦИИ (ПОЛЬЗОВАТЕЛИ) ---

@app.post("/register", response_model=schemas.UserResponse, tags=["Пользователи"])
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    # Хэшируем пароль для безопасности
    hashed_pass = models.User.hash_password(user_data.password)

    new_user = models.User(
        username=user_data.username,
        password_hash=hashed_pass
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", tags=["Пользователи"])
def login_user(response: Response, user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Логин пользователя и создание сессии (исправлено!)"""
    # 1. Ищем пользователя по логину
    user = db.query(models.User).filter(models.User.username == user_data.username).first()

    # 2. Если не нашли
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )

    # 3. Проверяем хэшированный пароль через метод из модели User (исправлено)
    if not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )

    # 4. Ставим куку сессии
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)

    return {"status": "success", "message": "Успешный вход", "username": user.username}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)