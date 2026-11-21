"""Check an authenticated user can open and close a ticket about a rental."""

import os
from uuid import uuid4

from smoke_license import AUTH_URL
from smoke_test import BOOKING_URL, RENTAL_URL, request, wait_until_ready


SUPPORT_URL = os.getenv("SUPPORT_URL", "http://127.0.0.1:8008")
TICKETS = "/api/support/tickets"


def main():
    wait_until_ready(AUTH_URL, BOOKING_URL, RENTAL_URL, SUPPORT_URL)
    credentials = {"email": f"{uuid4()}@example.test", "password": f"Smoke-{uuid4()}"}
    user = request(AUTH_URL, "/api/auth/register", {**credentials, "full_name": "Smoke Test"})
    token = request(AUTH_URL, "/api/auth/login", credentials)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    car = request(BOOKING_URL, "/api/cars", {
        "model": "Test Car", "plate_number": f"M{uuid4().hex[:4].upper()}777", "price_per_minute": 1500,
    })
    rental = request(RENTAL_URL, "/api/rentals", {"user_id": user["id"], "car_id": car["id"]})
    ticket = request(SUPPORT_URL, TICKETS, {
        "channel": "phone", "category": "accident", "rental_id": rental["id"],
        "subject": "Vehicle incident", "description": "Initial report",
    }, headers=headers)
    assert ticket["status"] == "open"
    assert ticket["car_id"] == car["id"]
    assert request(SUPPORT_URL, TICKETS, headers=headers)[0]["id"] == ticket["id"]

    path = f"{TICKETS}/{ticket['id']}"
    updated = request(SUPPORT_URL, path + "/messages", {"text": "Follow-up"}, headers=headers)
    assert updated["messages"][0]["text"] == "Follow-up"
    closed = request(SUPPORT_URL, path + "/close", {}, headers=headers)
    assert closed["status"] == "closed" and closed["closed_at"]
    assert request(SUPPORT_URL, path, headers=headers) == closed
    print("PASS: authenticated rental incident, message history and ticket closure")


if __name__ == "__main__":
    main()
