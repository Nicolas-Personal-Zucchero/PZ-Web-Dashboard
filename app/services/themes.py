from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.themes_production import Theme, Batch, Production

class ThemeProductionService:

    @staticmethod
    def get_theme_by_id(theme_id: int) -> Theme | None:
        return db.session.get(Theme, theme_id)

    @staticmethod
    def get_all_themes() -> list[Theme]:
        # Query diretta sulla tabella themes senza JOIN.
        stmt = db.select(Theme)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_theme(name: str) -> Theme:
        try:
            theme = Theme(name=name)
            db.session.add(theme)
            db.session.commit()
            return theme
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Il nome del tema deve essere univoco.") from e

    @staticmethod
    def update_theme(theme_id: int, name: str | None = None) -> Theme | None:
        theme = db.session.get(Theme, theme_id)
        if not theme:
            return None
        
        if name is not None:
            theme.name = name
        
        try:
            db.session.commit()
            return theme
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Il nome del tema deve essere univoco.") from e

    @staticmethod
    def get_batches_by_theme(theme_id: int) -> list[Batch]:
        # Recupera solo i batch specifici tramite filtering.
        stmt = db.select(Batch).where(Batch.theme_id == theme_id)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_batch_by_id(batch_id: int) -> Batch | None:
        return db.session.get(Batch, batch_id)

    @staticmethod
    def create_batch(theme_id: int, code: str) -> Batch:
        try:
            batch = Batch(theme_id=theme_id, code=code)
            db.session.add(batch)
            db.session.commit()
            return batch
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(
                "Il codice del lotto deve essere univoco."
            ) from e

    @staticmethod
    def update_batch(
        batch_id: int, 
        code: str | None = None,
    ) -> Batch | None:
        batch = db.session.get(Batch, batch_id)
        if not batch:
            return None
        
        if code is not None:
            batch.code = code
            
        try:
            db.session.commit()
            return batch
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Il codice del lotto deve essere univoco.") from e

    @staticmethod
    def get_productions_by_batch(batch_id: int) -> list[Production]:
        # Recupera solo le produzioni associate a un dato batch.
        stmt = db.select(Production).where(Production.batch_id == batch_id)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_production(
        batch_id: int, 
        date: datetime, 
        reel_batch: str, 
        quantity: Decimal, 
        operator_id: int
    ) -> Production:
        try:
            production = Production(
                batch_id=batch_id,
                date=date,
                reel_batch=reel_batch,
                quantity=quantity,
                operator_id=operator_id
            )
            db.session.add(production)
            db.session.commit()
            return production
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(
                "Violazione di vincolo: impossibile creare la produzione. Verificare l'esistenza del batch e dell'operatore."
            ) from e

    @staticmethod
    def update_production(
        production_id: int,
        date: datetime | None = None,
        reel_batch: str | None = None,
        quantity: Decimal | None = None,
        operator_id: int | None = None
    ) -> Production | None:
        production = db.session.get(Production, production_id)
        if not production:
            return None
        
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
            return production
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Violazione di vincolo durante l'aggiornamento della produzione.") from e