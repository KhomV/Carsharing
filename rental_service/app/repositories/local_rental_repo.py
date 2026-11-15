#НЕ ИСПОЛЬЗУЕТСЯ

from uuid import UUID

from app.models.rental import Rental, RentalStatus


rentals: list[Rental] = []


class RentalRepo:
    def get_by_id(self, rental_id: UUID) -> Rental:
        for rental in rentals:
            if rental.id == rental_id:
                return rental

        raise KeyError("Аренда не найдена")

    def get_unfinished_by_car_id(self, car_id: UUID) -> Rental | None:
        for rental in rentals:
            if (
                rental.car_id == car_id
                and rental.status != RentalStatus.FINISHED
            ):
                return rental

        return None

    def create(self, rental: Rental) -> Rental:
        rentals.append(rental)
        return rental

    def update(self, rental: Rental) -> Rental:
        for index, saved_rental in enumerate(rentals):
            if saved_rental.id == rental.id:
                rentals[index] = rental
                return rental

        raise KeyError("Аренда не найдена")