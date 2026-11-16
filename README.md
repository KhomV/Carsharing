# Carsharing Microservices Platform

Платформа каршеринга, построенная на базе микросервисной архитектуры с гибридным взаимодействием: синхронные REST-вызовы между сервисами и асинхронный обмен событиями через брокер сообщений RabbitMQ.

---

## 1. Обзор проекта

Микросервисы системы:
- **`rental_service`** (порт `18001`) — Управление жизненным циклом аренды автомобилей, расчёт тарифов и публикация событий в RabbitMQ.
- **`booking_service`** (порт `18002`) — Управление автопарком, поиск доступных машин на карте и бронирование ТС пользователями.
- **`payment_service`** (порт `8003`) — Обработка событий завершения поездки, выставление счетов, проведение оплат и защита от дубликатов.
- **`telemetry_service`** (порт `8004`) — Сбор телеметрии (GPS-координаты, топливо, пробег, зажигание, ручной тормоз) и передача на карту.

---

## 2. Стек технологий

- **Язык программирования:** Python 3.12
- **Веб-фреймворк:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Базы данных:** PostgreSQL 17 (*Database-per-Service*: 4 изолированные БД)
- **ORM и драйвер:** SQLAlchemy 2.0 + Psycopg 3 (`psycopg[binary] >= 3.2`)
- **Миграции БД:** Alembic
- **Валидация и конфиг:** Pydantic v2 + `pydantic-settings`
- **Брокер сообщений:** RabbitMQ 4 (Management) + `aio-pika` 9 (AMQP 0-9-1)
- **HTTP-клиент:** HTTPX (синхронное межсервисное взаимодействие)
- **Контейнеризация:** Docker, Docker Compose
- **Тестирование:** Pytest 8, Unittest Mock, изолированные БД (tmpfs)
- **CI/CD:** GitHub Actions

---

## 3. Веб-интерфейсы и сетевые порты

### Интерактивная документация API (Swagger UI)
- **Аренда:** [http://127.0.0.1:18001/docs](http://127.0.0.1:18001/docs)
- **Поиск и бронирование:** [http://127.0.0.1:18002/docs](http://127.0.0.1:18002/docs)
- **Оплата и счета:** [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs)
- **Телеметрия:** [http://127.0.0.1:8004/docs](http://127.0.0.1:8004/docs)

### Брокер сообщений RabbitMQ
- **Панель управления:** [http://127.0.0.1:15673](http://127.0.0.1:15673)
- **AMQP-порт:** `5673` (внутри docker-сети: `5672`)
- **Логин:** `carsharing`
- **Пароль:** `carsharing_password`

### Базы данных PostgreSQL (по умолчанию в Docker Compose)
| База данных | Порт хоста | Пользователь | Пароль |
| :--- | :---: | :--- | :--- |
| `rental_db` | `5433` | `rental_user` | `rental_password` |
| `booking_db` | `5435` | `booking_user` | `booking_password` |
| `payment_db` | `5434` | `payment_user` | `payment_password` |
| `telemetry_db` | `5436` | `telemetry_user` | `telemetry_password` |

---

## 4. Быстрый старт (Docker Compose)

> **Требования:** установленные [Docker](https://docs.docker.com/get-docker/) и Docker Compose.

```bash
# 1. Запуск всех сервисов (сборка образов и запуск в фоне)
docker compose up --build -d

# 2. Проверка статуса контейнеров
docker compose ps

# 3. Просмотр логов в реальном времени
docker compose logs -f
# или конкретного сервиса:
docker compose logs -f booking_service
docker compose logs -f telemetry_service

# 4. Проверка доступности всех 4 баз данных
python3 check_database.py

# 5. Приостановка контейнеров
docker compose stop

# 6. Полная остановка с удалением контейнеров и сетей
docker compose down

# 7. Полный сброс с удалением данных БД и очереди
docker compose down -v
```

---

## 5. Взаимодействие между сервисами

```
+-------------------+           REST (HTTPX)           +---------------------+
|  booking_service  | -------------------------------> |  telemetry_service  |
|   (порт 18002)    | <------------------------------- |     (порт 8004)     |
+-------------------+      актуальные координаты       +---------------------+
                                                                  |
                                                           данные с бортовых
                                                           систем авто

+-------------------+          AMQP (Direct)           +---------------------+
|  rental_service   | -------------------------------> |   payment_service   |
|   (порт 18001)    |         rental.finished          |     (порт 8003)     |
+-------------------+          через RabbitMQ          +---------------------+
```

1. **Синхронное взаимодействие (REST, HTTPX):**  
   При поиске доступных машин (`GET /api/cars/available`) `booking_service` синхронно запрашивает координаты и уровень топлива у `telemetry_service` (`GET /api/telemetry/cars`), формируя для клиента объект `CarWithCoordinates`.
2. **Асинхронное взаимодействие (AMQP, RabbitMQ):**  
   При завершении поездки (`POST /api/rentals/{id}/finish`) `rental_service` публикует персистентное событие `rental.finished` в exchange `ikbo-66_khomchenko_events`. Сервис `payment_service` слушает очередь `ikbo-66_khomchenko_payment`, выставляет счёт и защищает от дублирования оплат (идемпотентность по `rental_id`).

---

## 6. Тестирование

### А. Сквозной интеграционный тест (Smoke Test)
Проверяет взаимодействие всех 4 сервисов в реальном времени при запущенном `docker compose`:
1. Запись телеметрии (координаты, топливо).
2. Синхронный запрос карты в `booking_service`.
3. Бронирование и отмена бронирования.
4. Запуск аренды, пауза, возобновление и финиш.
5. Обработка события в RabbitMQ, выставление счёта и оплата.

```bash
python3 deploy/smoke_test.py
```

### Б. Комплексный прогон изолированных тестов (CI-скрипт)
Собирает тестовые образы, поднимает 4 БД PostgreSQL в tmpfs, накатывает миграции Alembic и запускает Unit + Integration тесты:
```bash
sh deploy/run_pr8.sh
```

### В. Пошаговый запуск тестов через `compose.tests.yaml`
```bash
# Сборка тестовых образов
docker compose -f compose.tests.yaml build

# Модульные тесты без БД
docker compose -f compose.tests.yaml run --rm --no-deps booking_tests python -m pytest tests/unit -v

# Запуск изолированных тестовых БД
docker compose -f compose.tests.yaml up -d --wait booking_test_db telemetry_test_db rental_test_db payment_test_db

# Интеграционные тесты (миграции + pytest)
docker compose -f compose.tests.yaml run --rm --no-deps booking_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v'

# Очистка тестового окружения
docker compose -f compose.tests.yaml down -v
```

---

## 7. Структура проекта

```text
Carsharing/
├── booking_service/      # Сервис поиска автопарка и бронирования (FastAPI, 18002)
├── telemetry_service/    # Сервис приёма и отдачи телеметрии авто (FastAPI, 8004)
├── rental_service/       # Сервис управления арендой машин (FastAPI, 18001)
├── payment_service/      # Сервис инвойсов и платежей (FastAPI, 8003)
├── deploy/               # Скрипты развёртывания, smoke-тестов и автоматизации
├── .github/workflows/    # Пайплайн GitHub Actions CI/CD
├── check_database.py     # Проверка подключения к базам данных
├── compose.server.yaml   # Конфигурация для боевого сервера (.env.server)
├── compose.tests.yaml    # Конфигурация для запуска изолированных тестов
├── docker-compose.yaml   # Основная конфигурация локальной разработки
├── requirements.txt      # Базовые зависимости проекта
└── README.md             # Документация проекта
```
