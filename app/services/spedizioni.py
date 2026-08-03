from datetime import date, datetime
from typing import List, Optional

from utils.utils import convert_datetime_to_italy_tz
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.spedizioni import SpedizionePreliminare, SpedizioneIdentificativo

class SpedizionePreliminareRepository:
    @staticmethod
    def get_pending() -> List[SpedizionePreliminare]:
        stmt = select(SpedizionePreliminare)\
            .where(SpedizionePreliminare.sent.is_(False))\
            .options(joinedload(SpedizionePreliminare.identificativi_rel))
        
        return db.session.execute(stmt).scalars().unique().all()

    @staticmethod
    def get_sent_filtered(
        data_invio: Optional[date] = None, 
        ragione_sociale: Optional[str] = None, 
        identificativo: Optional[str] = None
    ) -> List[SpedizionePreliminare]:
        
        stmt = select(SpedizionePreliminare)\
            .where(SpedizionePreliminare.sent.is_(True))\
            .options(joinedload(SpedizionePreliminare.identificativi_rel))

        if data_invio:
            stmt = stmt.where(func.date(SpedizionePreliminare.sent_at) == data_invio)

        if ragione_sociale:
            stmt = stmt.where(SpedizionePreliminare.ragione_sociale_cliente.ilike(f"%{ragione_sociale}%"))

        if identificativo:
            identificativo_pattern = f"%{identificativo}%"
            # Composizione espressione SQL per la ricerca testuale aggregata
            identificativo_expr = (
                SpedizioneIdentificativo.sigla + " " +
                SpedizioneIdentificativo.serie + "/" +
                SpedizioneIdentificativo.numero
            )
            stmt = stmt.where(
                SpedizionePreliminare.identificativi_rel.any(
                    or_(
                        SpedizioneIdentificativo.sigla.ilike(identificativo_pattern),
                        SpedizioneIdentificativo.serie.ilike(identificativo_pattern),
                        SpedizioneIdentificativo.numero.ilike(identificativo_pattern),
                        identificativo_expr.ilike(identificativo_pattern)
                    )
                )
            )

        result = db.session.execute(stmt).scalars().unique().all()
        for spedizione in result:
            spedizione.sent_at = convert_datetime_to_italy_tz(spedizione.sent_at)
        return result

    @staticmethod
    def get_by_id(spedizione_id: str) -> Optional[SpedizionePreliminare]:
        return db.session.get(SpedizionePreliminare, spedizione_id)

    @staticmethod
    def get_by_ids(spedizioni_ids: List[str]) -> List[SpedizionePreliminare]:
        if not spedizioni_ids:
            return []
            
        stmt = select(SpedizionePreliminare)\
            .where(SpedizionePreliminare.id.in_(spedizioni_ids))\
            .options(joinedload(SpedizionePreliminare.identificativi_rel))
            
        return db.session.execute(stmt).scalars().unique().all()

    @staticmethod
    def delete(spedizione: SpedizionePreliminare) -> None:
        try:
            db.session.delete(spedizione)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def mark_as_sent(spedizione: SpedizionePreliminare, timestamp: datetime) -> None:
        try:
            spedizione.sent = True
            spedizione.sent_at = timestamp
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e