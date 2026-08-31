from zoneinfo import ZoneInfo
from datetime import datetime

from extensions import db

class Ticket(db.Model):
    __tablename__ = 'tickets'

    code = db.Column(db.String(100), primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    assigned = db.Column(db.Boolean, default=False, nullable=False)

    assignment = db.relationship(
        'TicketAssignment',
        back_populates='ticket',
        uselist=False,
        cascade='all, delete-orphan'
    )

    @property
    def local_created_at(self) -> datetime:
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")
        
        if self.created_at.tzinfo is None:
            utc_aware = self.created_at.replace(tzinfo=utc_tz)
        else:
            utc_aware = self.created_at
            
        return utc_aware.astimezone(rome_tz)


class TicketAssignment(db.Model):
    __tablename__ = 'tickets_assignments'

    ticket_code = db.Column(
        db.String(100), 
        db.ForeignKey('tickets.code', ondelete='CASCADE'), 
        primary_key=True
    )
    
    customer_email = db.Column(db.String(255), nullable=False, index=True)
    assigned_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    assigned_with = db.Column(db.String(255), nullable=False)

    ticket = db.relationship(
        'Ticket',
        back_populates='assignment'
    )

    @property
    def local_assigned_at(self) -> datetime:
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")
        
        if self.assigned_at.tzinfo is None:
            utc_aware = self.assigned_at.replace(tzinfo=utc_tz)
        else:
            utc_aware = self.assigned_at
            
        return utc_aware.astimezone(rome_tz)