from datetime import datetime
from extensions import db
from . import TimezoneMixin

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
    quantity = db.Column(db.Integer, nullable=False)
    operator_id = db.Column(
        db.Integer,
        db.ForeignKey('employees.id', ondelete='RESTRICT'),
        nullable=False
    )

    batch = db.relationship(
        'Batch',
        back_populates='productions'
    )

    # Assunto che Employee sia registrato nel registry di SQLAlchemy
    operator = db.relationship('Employee')

    @property
    def local_date(self) -> datetime | None:
        return self._to_local_time(self.date)