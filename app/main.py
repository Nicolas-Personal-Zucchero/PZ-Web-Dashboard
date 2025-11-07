from flask import Flask, render_template

from routes.assegna_agente import assegna_agente_bp
from routes.recensioni import recensioni_bp
from routes.interventi import interventi_bp
from routes.registrazione_lotti import registrazione_lotti_bp
from routes.wip import wip_bp
from routes.agents_map import agents_map_bp
from routes.visualizza_lotti import visualizza_lotti_bp
from routes.visualizza_impianti import visualizza_impianti_bp
from routes.amministrazione import amministrazione_bp
from routes.backups import backups_bp

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Serve per flash()

app.register_blueprint(assegna_agente_bp)
app.register_blueprint(recensioni_bp)
app.register_blueprint(agents_map_bp)
app.register_blueprint(backups_bp)

amministrazione_bp.register_blueprint(registrazione_lotti_bp)
amministrazione_bp.register_blueprint(visualizza_lotti_bp)
amministrazione_bp.register_blueprint(visualizza_impianti_bp)
app.register_blueprint(amministrazione_bp)

wip_bp.register_blueprint(interventi_bp)
app.register_blueprint(wip_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)