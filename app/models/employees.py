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