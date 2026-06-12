import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SpedizionePreliminare(db.Model):
    __tablename__ = 'spedizioni_preliminari'

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    ragione_sociale_cliente = db.Column(db.String(255), nullable=False)
    cash_on_delivery = db.Column(db.Numeric(10, 2), default=False, nullable=True)
    data_ritiro = db.Column(db.Date, nullable=False)
    xml = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ragione_sociale_cliente": self.ragione_sociale_cliente,
            "cash_on_delivery": self.cash_on_delivery,
            "data_ritiro": self.data_ritiro.isoformat() if self.data_ritiro else None,
            "xml": self.xml
        }

def init_database(flask_app):
    db_dir = os.path.join(flask_app.instance_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(db_dir, 'database.db')}"
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(flask_app)

    with flask_app.app_context():
        db.create_all()