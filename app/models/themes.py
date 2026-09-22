from datetime import datetime
from extensions import db
from . import TimezoneMixin


class Theme(db.Model, TimezoneMixin):
    __tablename__ = "themes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    batches = db.relationship(
        "Batch",
        back_populates="theme",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

    @property
    def local_created_at(self) -> datetime | None:
        return self._to_local_time(self.created_at)
