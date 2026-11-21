"""Check the full rental -> RabbitMQ -> invoice -> payment flow and booking -> telemetry map integration."""
import json
import os
import time
import urllib.request
from uuid import uuid4

RENTAL_URL = os.getenv("RENTAL_URL", "http://127.0.0.1:8001")
BOOKING_URL = os.getenv("BOOKING_URL", "http://127.0.0.1:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://127.0.0.1:8003")
TELEMETRY_URL = os.getenv("TELEMETRY_URL", "http://127.0.0.1:8004")


def request(base, path, body=None, *, headers=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        base + path, data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def wait_until_ready(*service_urls):
    for base in service_urls:
        print(f"Waiting for {base} to become ready...")
        for attempt in range(60):
            try:
                request(base, "/openapi.json")
                print(f"Service at {base} is ready.")
                break
            except (OSError, ValueError) as err:
                if attempt == 59:
                    print(f"ERROR: Service at {base} failed to respond after 60 attempts: {err}")
                    raise
                time.sleep(2)


def main():
    wait_until_ready(RENTAL_URL, BOOKING_URL, PAYMENT_URL, TELEMETRY_URL)

    # 1. Telemetry and Booking test:
    car = request(BOOKING_URL, "/api/cars", {
        "model": "Exeed LX",
        "plate_number": f"M{str(uuid4())[:4].upper()}777",
        "price_per_minute": 1700,
    })
    car_id = car["id"]
    user_id = str(uuid4())

    telemetry = request(TELEMETRY_URL, "/api/telemetry", {
        "car_id": car_id,
        "latitude": 55.751244,
        "longitude": 37.618423,
        "fuel_level": 94,
        "mileage": 15200,
        "is_engine_on": False,
        "is_handbrake_engaged": True,
    })
    assert telemetry["car_id"] == car_id
    assert telemetry["fuel_level"] == 94

    available_cars = request(BOOKING_URL, "/api/cars/available")
    matched_car = next((c for c in available_cars if c["id"] == car_id), None)
    assert matched_car is not None, "Created car should appear in available cars list"
    assert matched_car["latitude"] == 55.751244, "Car coordinates should be populated synchronously from telemetry"
    assert matched_car["fuel_level"] == 94, "Car fuel level should match telemetry"

    booking = request(BOOKING_URL, "/api/bookings", {
        "user_id": user_id,
        "car_id": car_id,
        "duration_minutes": 25,
    })
    assert booking["status"] == "active"
    assert booking["car_id"] == car_id

    available_after_booking = request(BOOKING_URL, "/api/cars/available")
    assert not any(c["id"] == car_id for c in available_after_booking), "Booked car should not be in available list"

    cancelled_booking = request(BOOKING_URL, f"/api/bookings/{booking['id']}/cancel", {})
    assert cancelled_booking["status"] == "cancelled"

    available_after_cancel = request(BOOKING_URL, "/api/cars/available")
    assert any(c["id"] == car_id for c in available_after_cancel), "Cancelled car should return to available list"
    print("PASS: telemetry recording, sync coordinates fetch, car map display, booking, cancel")

    # 2. Rental and Payment flow test:
    rental = request(RENTAL_URL, "/api/rentals", {
        "user_id": user_id, "car_id": car_id,
    })
    path = f"/api/rentals/{rental['id']}"
    assert request(RENTAL_URL, path + "/pause", {})["status"] == "paused"
    assert request(RENTAL_URL, path + "/resume", {})["status"] == "active"
    finished = request(RENTAL_URL, path + "/finish", {})
    assert finished["status"] == "finished" and finished["total_amount"] > 0

    for attempt in range(30):
        matches = [i for i in request(PAYMENT_URL, "/api/invoices")
                   if i["rental_id"] == rental["id"]]
        if matches:
            break
        time.sleep(1)
    assert len(matches) == 1, "Expected one invoice for the finished rental"
    invoice = matches[0]
    assert invoice["amount"] == finished["total_amount"]
    assert invoice["user_id"] == rental["user_id"]

    request(RENTAL_URL, path + "/finish", {})
    time.sleep(2)
    matches = [i for i in request(PAYMENT_URL, "/api/invoices")
               if i["rental_id"] == rental["id"]]
    assert len(matches) == 1, "Duplicate event created another invoice"
    paid = request(PAYMENT_URL, f"/api/invoices/{invoice['id']}/pay", {})
    assert paid["status"] == "paid" and paid["paid_at"]
    print("PASS: rental, pause/resume, event, invoice, deduplication, payment")
    print(f"Test rental: {rental['id']}; invoice: {invoice['id']}")


if __name__ == "__main__":
    main()
