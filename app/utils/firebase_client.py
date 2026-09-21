import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_json_string = os.getenv("FIREBASE_SA_JSON")

if not firebase_json_string:
    raise ValueError("Variabile d'ambiente non trovata.")

cred_dict = json.loads(firebase_json_string)

cred = credentials.Certificate(cred_dict)

# Inizializza solo se non è già inizializzato
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()