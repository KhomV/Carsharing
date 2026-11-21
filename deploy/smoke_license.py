"""Check driver license verification and rental eligibility through real HTTP."""

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from smoke_test import request, wait_until_ready


AUTH_URL = os.getenv("AUTH_URL", "http://127.0.0.1:8005")
LICENSE_URL = os.getenv("LICENSE_URL", "http://127.0.0.1:8006")


def main():
    wait_until_ready(AUTH_URL, LICENSE_URL)
    credentials = {"email": f"{uuid4()}@example.test", "password": f"Smoke-{uuid4()}"}
    request(AUTH_URL, "/api/auth/register", {**credentials, "full_name": "Smoke Test"})
    token = request(AUTH_URL, "/api/auth/login", credentials)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    eligibility_path = "/api/auth/me/eligibility"
    assert request(AUTH_URL, eligibility_path, headers=headers) == {
        "eligible": False, "license_status": "missing",
    }

    today = datetime.now(timezone.utc).date()
    for days, expected in ((-1, "rejected"), (30, "verified")):
        document = request(LICENSE_URL, "/api/licenses", {
            "series": "0123", "number": "456789",
            "expires_on": (today + timedelta(days=days)).isoformat(),
        }, headers=headers)
        assert document["status"] == "pending"
        assert request(AUTH_URL, eligibility_path, headers=headers) == {
            "eligible": False, "license_status": "pending",
        }

        result = request(LICENSE_URL, f"/api/licenses/{document['id']}/verify", {}, headers=headers)
        assert result["status"] == expected
        assert request(AUTH_URL, eligibility_path, headers=headers) == {
            "eligible": expected == "verified", "license_status": expected,
        }

    print("PASS: authentication, driver license verification, rental eligibility")


if __name__ == "__main__":
    main()
