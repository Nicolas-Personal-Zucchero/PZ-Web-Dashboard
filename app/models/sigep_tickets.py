from zoneinfo import ZoneInfo
from datetime import datetime

from extensions import db


class Ticket(db.Model):
    __tablename__ = "tickets"

    code = db.Column(db.String(100), primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    customer_email = db.Column(db.String(255), nullable=True, index=True)
    assigned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    assigned_with = db.Column(db.String(255), nullable=True)
    hidden = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def local_created_at(self) -> datetime:
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")

        if self.created_at.tzinfo is None:
            utc_aware = self.created_at.replace(tzinfo=utc_tz)
        else:
            utc_aware = self.created_at

        return utc_aware.astimezone(rome_tz)

    @property
    def local_assigned_at(self) -> datetime | None:
        if not self.assigned_at:
            return None

        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")

        if self.assigned_at.tzinfo is None:
            utc_aware = self.assigned_at.replace(tzinfo=utc_tz)
        else:
            utc_aware = self.assigned_at

        return utc_aware.astimezone(rome_tz)
