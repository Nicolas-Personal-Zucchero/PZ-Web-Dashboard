from zoneinfo import ZoneInfo
from datetime import datetime
from extensions import db

class TimezoneMixin:
    def _to_local_time(self, dt_field: datetime) -> datetime | None:
        if not dt_field:
            return None
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")
        utc_aware = dt_field.replace(tzinfo=utc_tz) if dt_field.tzinfo is None else dt_field
        return utc_aware.astimezone(rome_tz)

class Theme(db.Model, TimezoneMixin):
    __tablename__ = 'themes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    batches = db.relationship(
        'Batch',
        back_populates='theme',
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy=True
    )

    @property
    def local_created_at(self) -> datetime | None:
        return self._to_local_time(self.created_at)

class Batch(db.Model, TimezoneMixin):
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(255), unique=True, nullable=False)
    theme_id = db.Column(
        db.Integer,
        db.ForeignKey('themes.id', ondelete='CASCADE'),
        nullable=False
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    theme = db.relationship(
        'Theme',
        back_populates='batches'
    )
    
    productions = db.relationship(
        'Production',
        back_populates='batch',
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy=True
    )

    @property
    def local_created_at(self) -> datetime | None:
        return self._to_local_time(self.created_at)

class Production(db.Model, TimezoneMixin):
    __tablename__ = 'productions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(
        db.Integer,
        db.ForeignKey('batches.id', ondelete='CASCADE'),
        nullable=False
    )
    date = db.Column(db.DateTime, nullable=False)
    reel_batch = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    operator_id = db.Column(
        db.Integer,
        db.ForeignKey('employees.id', ondelete='RESTRICT'),
        nullable=False
    )

    batch = db.relationship(
        'Batch',
        back_populates='productions'
    )

    operator = db.relationship('Employee')

    @property
    def local_date(self) -> datetime | None:
        return self._to_local_time(self.date)