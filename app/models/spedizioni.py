import enum
from extensions import db


class StatoSpedizione(enum.Enum):
    READY = "ready"
    SENDING = "sending"
    SENT = "sent"


class SpedizionePreliminare(db.Model):
    __tablename__ = "spedizioni_preliminari"
    __bind_key__ = "old_sqlite"

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    ragione_sociale_cliente = db.Column(db.String(255), nullable=False)
    nr_colli = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Numeric(10, 2), nullable=False)
    cash_on_delivery = db.Column(db.Numeric(10, 2), default=None, nullable=True)
    speed = db.Column(db.Boolean, default=False, nullable=False)
    xml = db.Column(db.Text, nullable=False)
    state = db.Column(
        db.Enum(StatoSpedizione, native_enum=False, length=50),
        default=StatoSpedizione.READY,
        nullable=False,
    )
    updated_state_at = db.Column(db.DateTime, nullable=True)

    # Relazione 1:N con eliminazione a cascata automatica dei dettagli
    identificativi_rel = db.relationship(
        "SpedizioneIdentificativo",
        backref="spedizione",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "identificativi": [
                f"{i.sigla} {i.serie}/{i.numero}" for i in self.identificativi_rel
            ],
            "ragione_sociale_cliente": self.ragione_sociale_cliente,
            "nr_colli": self.nr_colli,
            "peso": self.peso,
            "cash_on_delivery": self.cash_on_delivery,
            "speed": self.speed,
            "xml": self.xml,
            "state": self.state.value if self.state else None,
            "updated_state_at": self.updated_state_at,
        }


class SpedizioneIdentificativo(db.Model):
    __tablename__ = "spedizione_identificativi"
    __bind_key__ = "old_sqlite"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spedizione_id = db.Column(
        db.String(100),
        db.ForeignKey("spedizioni_preliminari.id", ondelete="CASCADE"),
        nullable=False,
    )
    sigla = db.Column(db.String(10), nullable=False)
    serie = db.Column(db.String(10), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    cod_conto = db.Column(db.String(20), nullable=False)
