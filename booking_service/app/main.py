from fastapi import FastAPI

from app.endpoints.booking_router import booking_router
from app.endpoints.car_router import car_router


app = FastAPI(
    title="Сервис поиска и бронирования автомобилей",
)

app.include_router(
    car_router,
    prefix="/api",
)
app.include_router(
    booking_router,
    prefix="/api",
)
