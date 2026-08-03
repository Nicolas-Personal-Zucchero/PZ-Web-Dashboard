from models.recensioni import Recensione
from extensions import db
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, select

class RecensioneService:
    @staticmethod
    def create(nome_cliente: str, email_cliente: str, lingua: str, mittente_id: int) -> Recensione:
        try:
            recensione = Recensione(
                nome_cliente=nome_cliente,
                email_cliente=email_cliente,
                lingua=lingua,
                mittente_id=mittente_id
            )
            db.session.add(recensione)
            db.session.commit()
            return recensione
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Errore di integrità: dipendente inesistente o vincolo violato") from e

    @staticmethod
    def get_filtered(nascosta: bool | None = None, lingua: str | None = None) -> list[Recensione]:
        stmt = select(Recensione).options(joinedload(Recensione.mittente))

        if nascosta is not None:
            stmt = stmt.where(Recensione.nascosta == nascosta)
        
        if lingua:
            stmt = stmt.where(Recensione.lingua == lingua)

        return db.session.scalars(stmt).all()

    @staticmethod
    def hide(recensione_id: int) -> bool:
        stmt = (
            update(Recensione)
            .where(Recensione.id == recensione_id)
            .values(nascosta=True)
        )
        result = db.session.execute(stmt)
        db.session.commit()
        
        return result.rowcount > 0