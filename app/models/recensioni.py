from zoneinfo import ZoneInfo
from datetime import datetime

from extensions import db

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=False)

    # Definizione esplicita e moderna
    reviews = db.relationship(
        'Review',
        back_populates='sender',
        lazy=True
    )

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False)
    creation_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    language = db.Column(db.String(3), nullable=False)
    
    sender_id = db.Column(
        db.Integer, 
        db.ForeignKey('employees.id'), 
        nullable=False
    )

    sender = db.relationship(
        'Employee',
        back_populates='reviews'
    )

    @property
    def local_creation_date(self) -> datetime:
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")
        
        if self.creation_date.tzinfo is None:
            utc_aware = self.creation_date.replace(tzinfo=utc_tz)
        else:
            utc_aware = self.creation_date
            
        return utc_aware.astimezone(rome_tz)