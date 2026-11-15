"""Check the full rental -> RabbitMQ -> invoice -> payment flow."""
import json
import os
import time
import urllib.request
from uuid import uuid4

RENTAL_URL = os.getenv("RENTAL_URL", "http://127.0.0.1:8001")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://127.0.0.1:8003")


def request(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        base + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def main():
    for base in (RENTAL_URL, PAYMENT_URL):
        for attempt in range(60):
            try:
                request(base, "/openapi.json")
                break
            except (OSError, ValueError):
                if attempt == 59:
                    raise
                time.sleep(2)

    rental = request(RENTAL_URL, "/api/rentals", {
        "user_id": str(uuid4()), "car_id": str(uuid4()),
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

    # Force a duplicate delivery and wait until the broker has processed it.
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
