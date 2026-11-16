import logging
from uuid import UUID

import httpx

from app.settings import settings


logger = logging.getLogger(__name__)


class TelemetryClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.telemetry_service_url).rstrip("/")

    def get_car_telemetry(self, car_id: UUID) -> dict | None:
        url = f"{self.base_url}/api/telemetry/cars/{car_id}"
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.json()
                if response.status_code == 404:
                    return None
                logger.warning(
                    "Телеметрия вернула неожиданный статус %s для авто %s",
                    response.status_code,
                    car_id,
                )
        except Exception as error:
            logger.warning(
                "Ошибка при запросе координат для авто %s: %s",
                car_id,
                error,
            )
        return None

    def get_all_cars_telemetry(self) -> dict[UUID, dict]:
        url = f"{self.base_url}/api/telemetry/cars"
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return {UUID(item["car_id"]): item for item in data}
                logger.warning(
                    "Телеметрия вернула статус %s при запросе всех авто",
                    response.status_code,
                )
        except Exception as error:
            logger.warning(
                "Ошибка при запросе телеметрии всех автомобилей: %s",
                error,
            )
        return {}
