# Практическая работа 8

Реализованы два вида тестирования для обоих сервисов:
- Unit: Pydantic-модели, стоимость, бизнес-правила, исключения и повторы событий.
  Репозитории заменены Mock; реальных подключений нет.
- Integration: репозитории с настоящей PostgreSQL 17 после Alembic-миграций.
  Проверены чтение/запись, обновление, уникальность и восстановление после ошибки.

Запуск из корня проекта:

```bash
docker compose -f compose.tests.yaml build
docker compose -f compose.tests.yaml run --rm --no-deps rental_tests python -m pytest tests/unit -v
docker compose -f compose.tests.yaml run --rm --no-deps payment_tests python -m pytest tests/unit -v
docker compose -f compose.tests.yaml up -d --wait rental_test_db payment_test_db
docker compose -f compose.tests.yaml run --rm --no-deps rental_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v'
docker compose -f compose.tests.yaml run --rm --no-deps payment_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v'
docker compose -f compose.tests.yaml down -v
```

У тестовой системы отдельное имя carsharing-tests, отдельная сеть и временные
PostgreSQL в tmpfs, без публикации портов. Каждый интеграционный тест использует
внешнюю транзакцию и savepoint; после теста изменения откатываются.
Фикстура допускает только явно разрешённые базы с суффиксом _test.
Рабочие базы и контейнеры Carsharing не используются.

Тесты включены в работу test GitHub Actions. Работа publish зависит от её успеха.
Дополнительно сохранена сквозная проверка deploy/smoke_test.py из работы 7.
