# Домашний сервер и CI/CD

Это альтернатива развёртыванию в Yandex Serverless из практической 7.
Согласуйте замену с преподавателем.

## Схема

Push в main -> GitHub Actions -> интеграционная проверка -> Docker Hub ->
домашний сервер проверяет образы каждые две минуты и обновляет контейнеры.
Pull request выполняет только проверки. Работы GitHub запускаются на ubuntu-latest,
а не на домашнем сервере.

## Docker Hub

Создайте публичные репозитории `khommv/carsharing-rental` и
`khommv/carsharing-payment`. Добавьте токен Docker Hub с правами Read & Write
в GitHub Actions secret `DOCKERHUB_TOKEN` репозитория KhomV/Carsharing.
Токен и серверные пароли не добавляйте в Git.

## Первоначальный запуск на Ubuntu

Код размещён в `/home/khomch/carsharing`.
`python3 deploy/init_env.py` создаёт `.env.server` один раз с правами 600.
Повторно этот скрипт не запускают: пароли уже используются базами.

```bash
cd /home/khomch/carsharing
docker compose --env-file .env.server -f compose.server.yaml up --build -d --wait
```

Базы и AMQP-порт доступны только внутри Docker. HTTP-приложения привязаны
к локальному адресу сервера, панель RabbitMQ — только к localhost.
API учебные и не имеют авторизации: проброс портов в интернет не настраивается.

## Автоматическое обновление

После первой успешной публикации ОБОИХ образов:

```bash
cd /home/khomch/carsharing
sh deploy/update.sh
python3 deploy/install_updater.py
```

Существующие записи crontab сохраняются. Скрипт использует flock, чтобы не
запускать параллельные обновления. Проверяет только образы приложений;
данные PostgreSQL и RabbitMQ остаются в именованных томах.
Compose пересоздаёт приложение, если изменился образ или конфигурация.
Последний результат: `deploy/update.log` (перезаписывается при каждой проверке).

Теги SHA коммита сохраняются в Docker Hub для ручного выбора версии.
Автообновление использует latest. Публикация двух тегов не атомарна:
сервисы должны сохранять совместимость формата событий между версиями.
Автоматического отката миграций нет. Перед изменением схемы БД делайте резервную копию.
Изменения compose.server.yaml и скриптов обновления переносятся на сервер отдельно;
планировщик автоматически обновляет только образы.

Отключение обновлений: `crontab -e`, удалить строку с `# carsharing-updater`.

## Проверка

```bash
docker compose --env-file .env.server -f compose.server.yaml ps
RENTAL_URL=http://192.168.0.36:8001 PAYMENT_URL=http://192.168.0.36:8003 python3 deploy/smoke_test.py
```

Проверка создаёт отдельную завершённую аренду и оплаченный счёт в БД.
Существующие записи не изменяются.

Адреса в домашней сети:
- Аренда: http://192.168.0.36:8001/docs
- Оплата: http://192.168.0.36:8003/docs

Остановка с сохранением данных:

```bash
docker compose --env-file .env.server -f compose.server.yaml stop
```

Minecraft остановлен для освобождения памяти. Его данные не изменяются.
Ручной повторный запуск: `sudo systemctl start minecraft`.
