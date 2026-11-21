from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app.clients.photo_store import StorageError, get_photo_store
from app.database import get_db
from app.endpoints.report_router import current_account_id
from app.main import app
from app.services import report_service


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.fail_at = None

    def put(self, report_id, photo, body):
        self.objects[report_id, photo.id] = body.read()
        if len(self.objects) == self.fail_at:
            raise StorageError("simulated upload failure")

    def remove(self, report_id, photo_id):
        self.objects.pop((report_id, photo_id), None)

    def read(self, report_id, photo):
        return self.objects[report_id, photo.id]


def test_report_and_photo_are_owner_scoped_and_failed_upload_can_retry(db, monkeypatch):
    account_id, booking_id, car_id = uuid4(), uuid4(), uuid4()
    viewer = account_id
    storage = MemoryStorage()
    app.dependency_overrides.update({
        get_db: lambda: db,
        get_photo_store: lambda: storage,
        current_account_id: lambda: viewer,
    })
    monkeypatch.setattr(report_service, "report_car_id", lambda *_args: car_id)
    image = BytesIO()
    Image.new("RGB", (2, 2)).save(image, "PNG")
    content = image.getvalue()
    files = [("photos", (f"{i}.png", content, "image/png")) for i in range(2)]
    path = f"/api/condition-reports/reference/before/{booking_id}"
    try:
        with TestClient(app) as client:
            storage.fail_at = 2
            assert client.post(path, files=files).status_code == 503
            assert not storage.objects
            assert client.get(path).status_code == 404

            storage.fail_at = None
            response = client.post(path, files=files)
            assert response.status_code == 201
            report = response.json()
            assert report["car_id"] == str(car_id)
            assert report["phase"] == "before"
            assert len(report["photos"]) == 2
            assert client.post(path, files=files).status_code == 409
            assert len(storage.objects) == 2
            assert client.get(path).json() == report

            report_path = f"/api/condition-reports/{report['id']}"
            photo_path = f"{report_path}/photos/{report['photos'][0]['id']}"
            download = client.get(photo_path)
            assert download.content == content
            assert download.headers["content-type"] == "image/png"
            assert download.headers["cache-control"] == "private, no-store"

            viewer = uuid4()
            assert client.get(path).status_code == 404
            assert client.get(report_path).status_code == 404
            assert client.get(photo_path).status_code == 404
    finally:
        app.dependency_overrides.clear()
