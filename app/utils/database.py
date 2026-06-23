import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SpedizionePreliminare(db.Model):
    __tablename__ = 'spedizioni_preliminari'

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    ragione_sociale_cliente = db.Column(db.String(255), nullable=False)
    nr_colli = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Numeric(10, 2), nullable=False)
    cash_on_delivery = db.Column(db.Numeric(10, 2), default=None, nullable=True)
    xml = db.Column(db.Text, nullable=False)

    # Relazione 1:N con eliminazione a cascata automatica dei dettagli
    identificativi_rel = db.relationship(
        'SpedizioneIdentificativo',
        backref='spedizione',
        cascade='all, delete-orphan',
        lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "identificativi": [i.fattura_identificativo for i in self.identificativi_rel],
            "ragione_sociale_cliente": self.ragione_sociale_cliente,
            "nr_colli": self.nr_colli,
            "peso": self.peso,
            "cash_on_delivery": self.cash_on_delivery,
            "xml": self.xml
        }

class SpedizioneIdentificativo(db.Model):
    __tablename__ = 'spedizione_identificativi'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spedizione_id = db.Column(
        db.String(100), 
        db.ForeignKey('spedizioni_preliminari.id', ondelete='CASCADE'), 
        nullable=False
    )
    fattura_identificativo = db.Column(db.String(100), nullable=False, index=True)

def init_database(flask_app):
    db_dir = os.path.join(flask_app.instance_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(db_dir, 'database.db')}"
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(flask_app)

    with flask_app.app_context():
        db.create_all()