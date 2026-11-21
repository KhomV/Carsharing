from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.clients.photo_store import PhotoStore, StorageError
from app.models.report import Photo
from app.services.report_service import inspect_photo


@pytest.mark.parametrize(("image_format", "expected"), [("JPEG", "image/jpeg"), ("PNG", "image/png")])
def test_photo_format_uses_decoded_content(image_format, expected):
    buffer = BytesIO()
    Image.new("RGB", (3, 3)).save(buffer, image_format)
    data = buffer.getvalue()
    upload = UploadFile(BytesIO(data), filename="fake.txt", size=len(data))
    photo = inspect_photo(upload)
    assert photo.content_type == expected
    assert photo.size_bytes == len(data)
    assert upload.file.read() == data


def test_non_image_is_rejected():
    upload = UploadFile(BytesIO(b"fake"), filename="fake.png", size=4)
    with pytest.raises(HTTPException) as error:
        inspect_photo(upload)
    assert error.value.status_code == 415


def test_storage_rejects_unexpected_photo_length():
    store = PhotoStore.__new__(PhotoStore)
    body = BytesIO(b"longer")

    class Client:
        def get_object(self, **_kwargs):
            return {"Body": body}

    store.client = Client()
    photo = Photo(id=uuid4(), content_type="image/png", size_bytes=4)
    with pytest.raises(StorageError, match="Unexpected photo size"):
        store.read(uuid4(), photo)
    assert body.closed
