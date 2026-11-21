from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from app.clients import source_client
from app.models.report import ReportPhase


@pytest.mark.parametrize(("phase", "status", "expected"), [
    (ReportPhase.BEFORE, "active", None),
    (ReportPhase.BEFORE, "expired", 409),
    (ReportPhase.BEFORE, "cancelled", 409),
    (ReportPhase.AFTER, "finished", None),
    (ReportPhase.AFTER, "active", 409),
    (ReportPhase.AFTER, "foreign", 404),
])
def test_reference_validation(monkeypatch, phase, status, expected):
    account_id, reference_id, car_id = uuid4(), uuid4(), uuid4()
    expiration = datetime.now(timezone.utc) + timedelta(days=-1 if status == "expired" else 1)

    def fetch(url):
        resource = "bookings" if phase == ReportPhase.BEFORE else "rentals"
        assert url.endswith(f"/api/{resource}/{reference_id}")
        return httpx.Response(200, request=httpx.Request("GET", url), json={
            "car_id": str(car_id),
            "user_id": str(uuid4() if status == "foreign" else account_id),
            "status": {"expired": "active", "foreign": "finished"}.get(status, status),
            "expires_at": expiration.isoformat(),
        })

    monkeypatch.setattr(source_client, "fetch", fetch)
    if expected is None:
        assert source_client.report_car_id(phase, reference_id, account_id) == car_id
    else:
        with pytest.raises(HTTPException) as error:
            source_client.report_car_id(phase, reference_id, account_id)
        assert error.value.status_code == expected
