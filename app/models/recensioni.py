from extensions import db

class Dipendente(db.Model):
    __tablename__ = 'dipendenti'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    reparto = db.Column(db.String(255), nullable=False)

    # Relazione 1:N
    recensioni_rel = db.relationship(
        'Recensione',
        backref='mittente',
        lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "reparto": self.reparto
        }

class Recensione(db.Model):
    __tablename__ = 'recensioni'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_cliente = db.Column(db.String(255), nullable=False)
    email_cliente = db.Column(db.String(255), nullable=False)
    
    # Utilizzo server_default per demandare il default al database (coerente con DBML default: `now()`)
    data_creazione = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    nascosta = db.Column(db.Boolean, default=False, nullable=False)
    
    lingua = db.Column(db.String(3), nullable=False)
    
    mittente_id = db.Column(
        db.Integer, 
        db.ForeignKey('dipendenti.id'), 
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome_cliente": self.nome_cliente,
            "email_cliente": self.email_cliente,
            "data_creazione": self.data_creazione.isoformat() if self.data_creazione else None,
            "nascosta": self.nascosta,
            "lingua": self.lingua,
            "mittente_id": self.mittente_id,
            "mittente_nome": self.mittente.nome if self.mittente else None 
        }