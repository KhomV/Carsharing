from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.car import Car, CarStatus
from app.schemas.car import CarTable


class CarRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, car_id: UUID) -> Car:
        row = self.db.get(CarTable, car_id)
        if row is None:
            raise KeyError("Автомобиль не найден")
        return Car.model_validate(row)

    def get_all(self) -> list[Car]:
        statement = select(CarTable).order_by(CarTable.created_at)
        rows = self.db.execute(statement).scalars().all()
        return [Car.model_validate(row) for row in rows]

    def get_available(self) -> list[Car]:
        statement = (
            select(CarTable)
            .where(CarTable.status == CarStatus.AVAILABLE.value)
            .order_by(CarTable.created_at)
        )
        rows = self.db.execute(statement).scalars().all()
        return [Car.model_validate(row) for row in rows]

    def create(self, car: Car) -> Car:
        row = CarTable(
            id=car.id,
            model=car.model,
            plate_number=car.plate_number,
            status=car.status.value,
            price_per_minute=car.price_per_minute,
            created_at=car.created_at,
        )

        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ValueError(
                "Автомобиль с таким госномером уже существует"
            ) from error

        self.db.refresh(row)
        return Car.model_validate(row)

    def update_status(self, car_id: UUID, status: CarStatus) -> Car:
        row = self.db.get(CarTable, car_id)
        if row is None:
            raise KeyError("Автомобиль не найден")

        row.status = status.value
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(row)
        return Car.model_validate(row)
