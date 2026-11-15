from sqlalchemy import create_engine, text


databases = {
    "Аренда": (
        "postgresql+psycopg://"
        "rental_user:rental_password@127.0.0.1:5433/rental_db"
    ),
    "Оплата": (
        "postgresql+psycopg://"
        "payment_user:payment_password@127.0.0.1:5434/payment_db"
    ),
}


for service_name, database_url in databases.items():
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database()")
            )

            database_name = result.scalar_one()

            print(f"{service_name}: подключение к {database_name} успешно")

    finally:
        engine.dispose()