from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.sigep_tickets import Ticket, TicketAssignment

class SigepTicketService:

    @staticmethod
    def create_ticket(code: str) -> Ticket:
        try:
            ticket = Ticket(code=code)
            db.session.add(ticket)
            db.session.commit()
            return ticket
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Errore di integrità: violazione vincolo PRIMARY KEY per il codice '{code}'") from e

    @staticmethod
    def get_available_tickets() -> list[Ticket]:
        stmt = select(Ticket).where(Ticket.assigned.is_(False))
        return list(db.session.scalars(stmt).all())

    @staticmethod
    def get_tickets_with_assignments() -> list[Ticket]:
        stmt = (
            select(Ticket)
            .options(joinedload(Ticket.assignment))
            .order_by(Ticket.created_at.desc())
        )
        return list(db.session.scalars(stmt).unique().all())