from utils.firebase_client import db
from firebase_admin import firestore
import re

class AssetService:
    _collection = db.collection("asset")

    def _natural_key(s):
        """Crea una chiave per l'ordinamento naturale: divide numeri e lettere"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    @staticmethod
    def get_all() -> list[dict]:
        docs = AssetService._collection.stream()
        entries = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        entries.sort(key=lambda x: AssetService._natural_key(x["nome"]))
        return entries

    @staticmethod
    def get(asset_id: str) -> dict | None:
        doc = AssetService._collection.document(asset_id).get()
        if not doc.exists:
            return None
        return {"id": doc.id, **doc.to_dict()}

    @staticmethod
    def create(nome: str, modello: str, tipologia: str, sede: str, posizione: str, intervallo_manutenzione: int, intervallo_pulizia: int) -> str:
        payload = {
            "nome": nome,
            "modello": modello,
            "tipologia": tipologia,
            "sede": sede,
            "posizione": posizione,
            "intervallo_manutenzione": intervallo_manutenzione,
            "intervallo_pulizia": intervallo_pulizia,
            "interventi": [],
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        _, doc_ref = AssetService._collection.add(payload)
        return doc_ref.id

    @staticmethod
    def update(asset_id: str, data: dict) -> bool:
        payload = data.copy()
        # Prevenzione side-effects: rimuove l'id se presente nel dizionario in ingresso
        payload.pop("id", None) 
        doc_ref = AssetService._collection.document(asset_id)
        
        try:
            doc_ref.update(payload)
            return True
        except Exception:
            return False

    @staticmethod
    def delete(asset_id: str) -> bool:
        doc_ref = AssetService._collection.document(asset_id)
        doc_ref.delete()
        return True

    @staticmethod
    def add_intervento(asset_id: str, intervento: dict) -> bool:
        doc_ref = AssetService._collection.document(asset_id)
        try:
            doc_ref.update({"interventi": firestore.ArrayUnion([intervento])})
            return True
        except Exception:
            return False

    @staticmethod
    @firestore.transactional
    def _transactional_update_intervento(transaction, doc_ref, intervento_id: str, update_data: dict) -> bool:
        snapshot = doc_ref.get(transaction=transaction)
        if not snapshot.exists:
            return False
        
        data = snapshot.to_dict()
        interventi = data.get("interventi", [])
        
        updated = False
        for i, intervento in enumerate(interventi):
            if intervento.get("id") == intervento_id:
                interventi[i].update(update_data)
                updated = True
                break
        
        if not updated:
            return False
            
        transaction.update(doc_ref, {"interventi": interventi})
        return True

    @staticmethod
    def update_intervento(asset_id: str, intervento_id: str, update_data: dict) -> bool:
        transaction = db.transaction()
        doc_ref = AssetService._collection.document(asset_id)
        return AssetService._transactional_update_intervento(transaction, doc_ref, intervento_id, update_data)

    @staticmethod
    @firestore.transactional
    def _transactional_delete_intervento(transaction, doc_ref, intervento_id: str) -> bool:
        snapshot = doc_ref.get(transaction=transaction)
        if not snapshot.exists:
            return False
            
        data = snapshot.to_dict()
        interventi = data.get("interventi", [])
        
        # Filtra l'array in memoria rimuovendo il target
        filtered_interventi = [i for i in interventi if i.get("id") != intervento_id]
        
        if len(interventi) == len(filtered_interventi):
            return False
            
        transaction.update(doc_ref, {"interventi": filtered_interventi})
        return True

    @staticmethod
    def delete_intervento(asset_id: str, intervento_id: str) -> bool:
        transaction = db.transaction()
        doc_ref = AssetService._collection.document(asset_id)
        return AssetService._transactional_delete_intervento(transaction, doc_ref, intervento_id)