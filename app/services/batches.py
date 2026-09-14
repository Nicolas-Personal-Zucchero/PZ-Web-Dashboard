from typing import Optional
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.batches import Batch

class BatchService:

    @staticmethod
    def get_batches_by_theme(theme_id: int) -> list[Batch]:
        stmt = db.select(Batch).where(Batch.theme_id == theme_id)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_batch_by_id(batch_id: int) -> Batch | None:
        return db.session.get(Batch, batch_id)

    @staticmethod
    def create_batch(theme_id: int, code: str) -> Optional[Batch]:
        try:
            batch = Batch(theme_id=theme_id, code=code)
            db.session.add(batch)
            db.session.commit()
            return batch
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def update_batch(batch_id: int, code: str | None = None) -> bool:
        batch = db.session.get(Batch, batch_id)
        if not batch:
            return False
        
        if code is not None:
            batch.code = code
            
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def delete_batch(batch_id: int) -> bool:
        batch = db.session.get(Batch, batch_id)
        if not batch:
            return False
            
        try:
            db.session.delete(batch)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False