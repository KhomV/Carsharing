from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.report import ReportPhase
from app.schemas.report import ReportTable


class ReportRepo:
    def __init__(self, db: Session):
        self.db = db

    def reserve(self, report: ReportTable) -> bool:
        statement = (
            insert(ReportTable)
            .values(
                id=report.id, account_id=report.account_id, car_id=report.car_id,
                reference_id=report.reference_id, phase=report.phase,
                created_at=report.created_at, photos=report.photos,
            )
            .on_conflict_do_nothing(constraint="uq_condition_reports_reference")
            .returning(ReportTable.id)
        )
        return self.db.scalar(statement) is not None

    def find_by_id(self, account_id: UUID, report_id: UUID) -> ReportTable | None:
        return self.db.scalar(select(ReportTable).where(
            ReportTable.account_id == account_id, ReportTable.id == report_id,
        ))

    def find_by_reference(
        self, account_id: UUID, phase: ReportPhase, reference_id: UUID,
    ) -> ReportTable | None:
        return self.db.scalar(select(ReportTable).where(
            ReportTable.account_id == account_id, ReportTable.phase == phase.value,
            ReportTable.reference_id == reference_id,
        ))

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
