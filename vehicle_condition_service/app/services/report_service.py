from datetime import datetime, timezone
from logging import getLogger
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.clients.photo_store import PhotoStore, StorageError, get_photo_store
from app.clients.source_client import report_car_id
from app.database import get_db
from app.models.report import ConditionReport, Photo, ReportPhase
from app.repositories.db_report_repo import ReportRepo
from app.schemas.report import ReportTable


logger = getLogger(__name__)
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 20_000_000
IMAGE_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png"}


def inspect_photo(upload: UploadFile) -> Photo:
    size = upload.size
    if not size:
        raise HTTPException(status_code=422, detail="Empty photo")
    if size > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Each photo must be at most 5 MiB")
    try:
        with Image.open(upload.file, formats=list(IMAGE_TYPES)) as image:
            if image.width * image.height > MAX_PHOTO_PIXELS:
                raise HTTPException(status_code=413, detail="Photo has too many pixels")
            if getattr(image, "n_frames", 1) != 1:
                raise HTTPException(status_code=415, detail="Animated images are not supported")
            content_type = IMAGE_TYPES[image.format]
            image.load()
    except Image.DecompressionBombError as error:
        raise HTTPException(status_code=413, detail="Photo has too many pixels") from error
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as error:
        raise HTTPException(status_code=415, detail="Expected a valid JPEG or PNG photo") from error
    finally:
        upload.file.seek(0)
    return Photo(id=uuid4(), content_type=content_type, size_bytes=size)


class ReportService:
    def __init__(self, db: Session = Depends(get_db), store: PhotoStore = Depends(get_photo_store)):
        self.repo = ReportRepo(db)
        self.store = store

    def create(
        self, account_id: UUID, phase: ReportPhase, reference_id: UUID, photos: list[UploadFile],
    ) -> ConditionReport:
        car_id = report_car_id(phase, reference_id, account_id)
        report = ConditionReport(
            id=uuid4(), phase=phase, reference_id=reference_id, car_id=car_id,
            created_at=datetime.now(timezone.utc), photos=[inspect_photo(photo) for photo in photos],
        )
        row = ReportTable(
            id=report.id, account_id=account_id, car_id=car_id, reference_id=reference_id,
            phase=phase.value, created_at=report.created_at,
            photos=[photo.model_dump(mode="json") for photo in report.photos],
        )
        if not self.repo.reserve(row):
            self.repo.rollback()
            raise HTTPException(status_code=409, detail="A report already exists for this reference")

        attempted = []
        try:
            for photo, upload in zip(report.photos, photos, strict=True):
                attempted.append(photo.id)
                self.store.put(report.id, photo, upload.file)
        except StorageError as error:
            self.repo.rollback()
            for photo_id in attempted:
                try:
                    self.store.remove(report.id, photo_id)
                except StorageError:
                    logger.warning("Could not remove photo %s from failed report %s", photo_id, report.id)
            raise HTTPException(status_code=503, detail="Photo storage unavailable") from error

        self.repo.commit()
        return report

    def get(self, account_id: UUID, report_id: UUID) -> ConditionReport:
        report = self.repo.find_by_id(account_id, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Condition report not found")
        return ConditionReport.model_validate(report)

    def get_by_reference(self, account_id: UUID, phase: ReportPhase, reference_id: UUID) -> ConditionReport:
        report = self.repo.find_by_reference(account_id, phase, reference_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Condition report not found")
        return ConditionReport.model_validate(report)

    def download(self, account_id: UUID, report_id: UUID, photo_id: UUID) -> tuple[Photo, bytes]:
        report = self.get(account_id, report_id)
        photo = next((item for item in report.photos if item.id == photo_id), None)
        if photo is None:
            raise HTTPException(status_code=404, detail="Photo not found")
        try:
            return photo, self.store.read(report_id, photo)
        except StorageError as error:
            raise HTTPException(status_code=503, detail="Photo storage unavailable") from error
