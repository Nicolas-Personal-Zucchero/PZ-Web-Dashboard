from datetime import datetime
from extensions import db
from . import TimezoneMixin


class Batch(db.Model, TimezoneMixin):
    __tablename__ = "batches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(255), nullable=False)
    theme_id = db.Column(
        db.Integer, db.ForeignKey("themes.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    theme = db.relationship("Theme", back_populates="batches")

    productions = db.relationship(
        "Production",
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

    @property
    def local_created_at(self) -> datetime | None:
        return self._to_local_time(self.created_at)
