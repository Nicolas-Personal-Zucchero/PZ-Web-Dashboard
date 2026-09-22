from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.productions import Production


class ProductionService:

    @staticmethod
    def get_productions_by_batch(batch_id: int) -> list[Production]:
        stmt = (
            db.select(Production)
            .where(Production.batch_id == batch_id)
            .order_by(Production.date)
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_production(
        batch_id: int,
        date: datetime,
        reel_batch: str,
        quantity: Decimal,
        operator_id: int,
    ) -> Optional[Production]:
        try:
            production = Production(
                batch_id=batch_id,
                date=date,
                reel_batch=reel_batch,
                quantity=quantity,
                operator_id=operator_id,
            )
            db.session.add(production)
            db.session.commit()
            return production
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def update_production(
        production_id: int,
        date: datetime | None = None,
        reel_batch: str | None = None,
        quantity: Decimal | None = None,
        operator_id: int | None = None,
    ) -> bool:
        production = db.session.get(Production, production_id)
        if not production:
            return False

        if date is not None:
            production.date = date
        if reel_batch is not None:
            production.reel_batch = reel_batch
        if quantity is not None:
            production.quantity = quantity
        if operator_id is not None:
            production.operator_id = operator_id

        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def delete_production(production_id: int) -> bool:
        production = db.session.get(Production, production_id)
        if not production:
            return False

        try:
            db.session.delete(production)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False
