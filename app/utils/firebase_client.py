import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("/app/data/serviceAccountKey.json")

# Inizializza solo se non è già inizializzato
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()