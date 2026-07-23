# Education Platform API

Backend образовательной платформы для организации учебного процесса, решения заданий и анализа результатов учеников.

Платформа предназначена для учеников, преподавателей и администраторов образовательных организаций. Она позволит управлять школами и классами, размещать учебные задания, сохранять попытки решения, отслеживать прогресс и формировать персональные подборки на основе слабых тем ученика.

## Основные возможности платформы

* управление пользователями, школами и классами;
* разграничение доступа для учеников, преподавателей и администраторов;
* создание и хранение учебных заданий;
* тренировочный и контрольный режимы;
* сохранение истории попыток;
* статистика по ученикам и классам;
* определение слабых тем;
* персонализированный подбор заданий;
* фоновый пересчёт аналитики;
* кеширование часто запрашиваемых данных.

## Стек

* Python 3.12+
* FastAPI
* PostgreSQL
* SQLAlchemy 2.x
* AsyncPG
* Alembic
* Pydantic
* Redis
* Celery
* Docker
* Docker Compose
* pytest
* Ruff
* Pyright
* GitHub Actions

## Архитектура

Приложение строится по многослойной архитектуре:

```text
HTTP-запрос
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

Структура проекта:

```text
app/
├── api/
│   └── routers/          # HTTP-endpoint
├── core/                 # Конфигурация и логирование
├── db/                   # Подключение к БД, сессии и ORM Base
├── models/               # ORM-модели SQLAlchemy
├── repositories/         # Запросы к базе данных
├── schemas/              # Pydantic-схемы
├── services/             # Бизнес-логика
└── main.py               # Точка входа FastAPI

tests/                    # Автоматические тесты
compose.yaml              # Docker-инфраструктура
Dockerfile                # Образ приложения
pyproject.toml            # Зависимости и конфигурация инструментов
```

## Локальный запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/sumarokovlyosha-ops/education-platform.git
cd education-platform-api
```

### 2. Создать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Для Windows:

```bash
.venv\Scripts\activate
```

### 3. Установить зависимости

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 4. Создать файл окружения

```bash
cp .env.example .env
```

Пример конфигурации:

```env
APP_NAME=Education Platform API
APP_VERSION=0.1.0
APP_DEBUG=false
APP_LOG_LEVEL=INFO

POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_DB=education_platform
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

Настоящий файл `.env` не должен попадать в Git.

Если порт `5432` свободен, можно использовать:

```env
POSTGRES_PORT=5432
```

### 5. Запустить PostgreSQL

```bash
docker compose up -d postgres
```

Проверить состояние контейнера:

```bash
docker compose ps
```

### 6. Запустить API

```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Проверка работы

Проверить, что FastAPI запущен:

```bash
curl http://127.0.0.1:8000/health/live
```

Проверить соединение приложения с PostgreSQL:

```bash
curl http://127.0.0.1:8000/health/ready
```

Успешный ответ:

```json
{
  "status": "ok"
}
```

## Проверка качества кода

Форматирование:

```bash
ruff format .
```

Линтер:

```bash
ruff check .
```

Статическая проверка типов:

```bash
pyright
```

Тесты:

```bash
pytest
```
