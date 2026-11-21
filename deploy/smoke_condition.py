"""Check before and after reports, including the round trip through S3."""

import json
import os
import struct
import urllib.request
import zlib
from uuid import uuid4

from smoke_license import AUTH_URL
from smoke_test import BOOKING_URL, RENTAL_URL, request, wait_until_ready


CONDITION_URL = os.getenv("CONDITION_URL", "http://127.0.0.1:8007")
REPORTS = "/api/condition-reports"


def make_photo():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )


def check_report(phase, reference_id, car_id, headers):
    photo = make_photo()
    boundary = uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="photos"; filename="car.png"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode() + photo + f"\r\n--{boundary}--\r\n".encode()
    reference_path = f"{REPORTS}/reference/{phase}/{reference_id}"
    upload = urllib.request.Request(
        CONDITION_URL + reference_path, data=body,
        headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(upload, timeout=20) as response:
        assert response.status == 201
        report = json.load(response)
    assert report["phase"] == phase and report["car_id"] == car_id
    assert request(CONDITION_URL, reference_path, headers=headers) == report
    photo_id = report["photos"][0]["id"]
    download = urllib.request.Request(
        f"{CONDITION_URL}{REPORTS}/{report['id']}/photos/{photo_id}", headers=headers,
    )
    with urllib.request.urlopen(download, timeout=20) as response:
        assert response.headers.get_content_type() == "image/png"
        assert response.read() == photo


def main():
    wait_until_ready(AUTH_URL, BOOKING_URL, RENTAL_URL, CONDITION_URL)
    credentials = {"email": f"{uuid4()}@example.test", "password": f"Smoke-{uuid4()}"}
    user = request(AUTH_URL, "/api/auth/register", {**credentials, "full_name": "Smoke Test"})
    token = request(AUTH_URL, "/api/auth/login", credentials)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    car = request(BOOKING_URL, "/api/cars", {
        "model": "Test Car", "plate_number": f"M{uuid4().hex[:4].upper()}777", "price_per_minute": 1500,
    })
    reference = {"user_id": user["id"], "car_id": car["id"]}
    booking = request(BOOKING_URL, "/api/bookings", reference)
    check_report("before", booking["id"], car["id"], headers)
    rental = request(RENTAL_URL, "/api/rentals", reference)
    request(RENTAL_URL, f"/api/rentals/{rental['id']}/finish", {})
    check_report("after", rental["id"], car["id"], headers)
    print("PASS: before and after vehicle condition reports and private photo storage")


if __name__ == "__main__":
    main()
