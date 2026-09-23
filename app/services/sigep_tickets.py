from datetime import datetime, timezone
from sqlalchemy import update, func, select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.sigep_tickets import Ticket


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
            raise ValueError(
                f"Errore di integrità: violazione vincolo per il codice '{code}'"
            ) from e

    @staticmethod
    def get_available_count() -> int:
        """Restituisce il numero di biglietti non ancora assegnati e non nascosti."""
        stmt = (
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.customer_email.is_(None))
            .where(Ticket.hidden.is_(False))
        )
        return db.session.scalar(stmt) or 0

    @staticmethod
    def get_available_tickets() -> list[Ticket]:
        """Restituisce la lista dei biglietti disponibili e non nascosti."""
        stmt = (
            select(Ticket)
            .where(Ticket.customer_email.is_(None))
            .where(Ticket.hidden.is_(False))
        )
        return list(db.session.scalars(stmt).all())

    @staticmethod
    def get_tickets_with_assignments() -> list[Ticket]:
        """Restituisce solo i biglietti assegnati e non nascosti, ordinati dal più recente."""
        stmt = (
            select(Ticket)
            .where(Ticket.customer_email.is_not(None))
            .where(Ticket.hidden.is_(False))
            .order_by(Ticket.assigned_at.desc())
        )
        return list(db.session.scalars(stmt).all())

    @staticmethod
    def get_assigned_summary() -> list[dict]:
        """Raggruppa le assegnazioni per email con conteggio e codici, ignorando quelli nascosti."""
        stmt = (
            select(Ticket.customer_email, Ticket.code)
            .where(Ticket.customer_email.is_not(None))
            .where(Ticket.hidden.is_(False))
        )
        rows = db.session.execute(stmt).all()

        assigned_map = {}
        for email, code in rows:
            if email not in assigned_map:
                assigned_map[email] = {"email": email, "count": 0, "codes": []}

            assigned_map[email]["count"] += 1
            assigned_map[email]["codes"].append(code)

        return sorted(assigned_map.values(), key=lambda x: x["count"], reverse=True)

    @staticmethod
    def assign_tickets(
        count: int, email: str, assigned_with: str = "personalzucchero.local"
    ) -> list[str]:
        """Assegna in modo transazionale 'count' biglietti non nascosti all'email indicata."""
        try:
            stmt = (
                select(Ticket)
                .where(Ticket.customer_email.is_(None))
                .where(Ticket.hidden.is_(False))
                .limit(count)
            )
            tickets = list(db.session.scalars(stmt).all())

            if len(tickets) < count:
                raise ValueError(
                    f"Non ci sono abbastanza biglietti disponibili. Richiesti: {count}, Disponibili: {len(tickets)}"
                )

            assigned_codes = []
            now = datetime.now(timezone.utc)

            for ticket in tickets:
                ticket.customer_email = email
                ticket.assigned_at = now
                ticket.assigned_with = assigned_with
                assigned_codes.append(ticket.code)

            db.session.commit()
            return assigned_codes
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def bulk_create_tickets(codes: list[str]) -> int:
        """Inserisce una lista di codici ignorando i duplicati già presenti (nascosti e non)."""
        clean_codes = {c.strip() for c in codes if c and c.strip()}
        if not clean_codes:
            return 0

        try:
            stmt = select(Ticket.code).where(Ticket.code.in_(clean_codes))
            existing_codes = set(db.session.scalars(stmt).all())

            to_insert = [
                Ticket(code=code) for code in clean_codes if code not in existing_codes
            ]

            if to_insert:
                db.session.add_all(to_insert)
                db.session.commit()

            return len(to_insert)
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def clear_all_tickets() -> int:
        """Nasconde tutti i biglietti (soft delete) impostando hidden = True."""
        try:
            stmt = update(Ticket).where(Ticket.hidden.is_(False)).values(hidden=True)
            result = db.session.execute(stmt)
            db.session.commit()
            return result.rowcount or 0
        except Exception:
            db.session.rollback()
            raise
