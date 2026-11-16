================================================================================
                    CARSHARING MICROSERVICES PLATFORM
================================================================================

1. ОБЗОР ПРОЕКТА
----------------
Платформа каршеринга, построенная на базе микросервисной архитектуры с гибридным
взаимодействием: синхронные REST-вызовы между сервисами и асинхронный обмен
событиями через брокер сообщений RabbitMQ.

Микросервисы системы:
  * rental_service    (порт 8001) - Управление жизненным циклом аренды автомобилей,
                                    расчёт тарифов и публикация событий в RabbitMQ.
  * booking_service   (порт 8002) - Управление автопарком, поиск доступных машин на
                                    карте и бронирование ТС пользователями.
  * payment_service   (порт 8003) - Обработка событий завершения поездки, выставление
                                    счетов, проведение оплат и защита от дубликатов.
  * telemetry_service (порт 8004) - Сбор телеметрии (GPS-координаты, топливо, пробег,
                                    зажигание, ручной тормоз) и передача на карту.

2. СТЕК ТЕХНОЛОГИЙ
------------------
  * Язык программирования:  Python 3.12
  * Веб-фреймворк:          FastAPI + Uvicorn
  * Базы данных:            PostgreSQL 17 (Database-per-Service: 4 изолированные БД)
  * ORM и драйвер:          SQLAlchemy 2.0 + Psycopg 3 (psycopg[binary] >= 3.2)
  * Миграции БД:            Alembic
  * Валидация и конфиг:     Pydantic v2 + pydantic-settings
  * Брокер сообщений:       RabbitMQ 4 (Management) + aio-pika 9 (AMQP 0-9-1)
  * HTTP-клиент:            HTTPX (синхронное межсервисное взаимодействие)
  * Контейнеризация:        Docker, Docker Compose
  * Тестирование:           Pytest 8, Unittest Mock, изолированные БД (tmpfs)
  * CI/CD:                  GitHub Actions

3. ВЕБ-ИНТЕРФЕЙСЫ И СЕТЕВЫЕ ПОРТЫ
---------------------------------
  Интерактивная документация API (Swagger UI):
    - Аренда:                 http://127.0.0.1:8001/docs
    - Поиск и бронирование:   http://127.0.0.1:8002/docs
    - Оплата и счета:         http://127.0.0.1:8003/docs
    - Телеметрия:             http://127.0.0.1:8004/docs

  Брокер сообщений RabbitMQ:
    - Веб-панель управления:  http://127.0.0.1:15673
    - AMQP-порт:              5673 (внутри сети: 5672)
    - Логин:                  carsharing
    - Пароль:                 carsharing_password

  Базы данных PostgreSQL (по умолчанию в docker-compose):
    - rental_db:              порт 5433 (user: rental_user, pass: rental_password)
    - booking_db:             порт 5435 (user: booking_user, pass: booking_password)
    - payment_db:             порт 5434 (user: payment_user, pass: payment_password)
    - telemetry_db:           порт 5436 (user: telemetry_user, pass: telemetry_password)

4. БЫСТРЫЙ СТАРТ (DOCKER COMPOSE)
---------------------------------
  Требования: установленные Docker и Docker Compose.

  Запуск всех сервисов (сборка образов и запуск в фоне):
    $ docker compose up --build -d

  Проверка статуса контейнеров:
    $ docker compose ps

  Просмотр логов в реальном времени:
    $ docker compose logs -f
    $ docker compose logs -f booking_service
    $ docker compose logs -f telemetry_service

  Проверка доступности всех 4 баз данных:
    $ python3 check_database.py

  Приостановка контейнеров:
    $ docker compose stop

  Полная остановка с удалением контейнеров и сетей:
    $ docker compose down

  Сброс данных (очистка томов баз данных и очереди):
    $ docker compose down -v

5. ВЗАИМОДЕЙСТВИЕ МЕЖДУ СЕРВИСАМИ
---------------------------------
  1. Синхронное взаимодействие (REST, HTTPX):
     При поиске доступных машин (GET /api/cars/available) booking_service
     синхронно обращается к telemetry_service (GET /api/telemetry/cars) для
     получения актуальных координат, запаса топлива и параметров автомобиля,
     формируя для карты единый объект CarWithCoordinates.

  2. Асинхронное взаимодействие (AMQP, RabbitMQ):
     При завершении поездки (POST /api/rentals/{id}/finish) rental_service
     публикует персистентное событие rental.finished в direct exchange
     "ikbo-66_khomchenko_events". Сервис payment_service слушает очередь
     "ikbo-66_khomchenko_payment", гарантируя обработку сообщений (ack/nack)
     и защиту от дублирования счетов (идемпотентность по rental_id).

6. ТЕСТИРОВАНИЕ
---------------
  А. Сквозной интеграционный тест (Smoke Test):
     Проверяет взаимодействие всех 4 сервисов в реальном времени:
       1) Запись телеметрии (координаты, топливо).
       2) Синхронный запрос карты в booking_service.
       3) Бронирование и отмена бронирования.
       4) Запуск аренды, пауза, возобновление и финиш.
       5) Обработка события в RabbitMQ, выставление счёта и оплата.
     Запуск (при работающем docker compose):
       $ python3 deploy/smoke_test.py

  Б. Комплексный прогон изолированных тестов (CI-скрипт):
     Собирает тестовые образы, поднимает 4 БД PostgreSQL в tmpfs,
     накатывает миграции Alembic и прогоняет Unit + Integration тесты:
       $ sh deploy/run_pr8.sh

  В. Пошаговый запуск через compose.tests.yaml:
     $ docker compose -f compose.tests.yaml build
     $ docker compose -f compose.tests.yaml run --rm --no-deps booking_tests python -m pytest tests/unit -v
     $ docker compose -f compose.tests.yaml up -d --wait booking_test_db telemetry_test_db rental_test_db payment_test_db
     $ docker compose -f compose.tests.yaml run --rm --no-deps booking_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v'
     $ docker compose -f compose.tests.yaml down -v

7. СТРУКТУРА ПРОЕКТА
--------------------
  Carsharing/
  ├── booking_service/      - Сервис поиска автопарка и бронирования (FastAPI, 8002)
  ├── telemetry_service/    - Сервис приёма и отдачи телеметрии авто (FastAPI, 8004)
  ├── rental_service/       - Сервис управления арендой машин (FastAPI, 8001)
  ├── payment_service/      - Сервис инвойсов и платежей (FastAPI, 8003)
  ├── deploy/               - Скрипты развёртывания, smoke-тестов и автоматизации
  ├── .github/workflows/    - Пайплайн GitHub Actions CI/CD
  ├── check_database.py     - Проверка подключения к базам данных
  ├── compose.server.yaml   - Конфигурация для боевого сервера (.env.server)
  ├── compose.tests.yaml    - Конфигурация для запуска изолированных тестов
  ├── docker-compose.yaml   - Основная конфигурация локальной разработки
  ├── requirements.txt      - Базовые зависимости проекта
  └── README.txt            - Настоящий файл документации
