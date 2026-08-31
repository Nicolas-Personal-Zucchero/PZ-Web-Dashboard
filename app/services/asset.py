from datetime import datetime
from utils.firebase_client import db
from firebase_admin import firestore
import re
from typing import Optional

class AssetService:
    _BATCH_SIZE = 400
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
    def create(nome: str, modello: str, tipologia: str, sede: str, posizione: str, intervallo_controllo_periodico: int, intervallo_pulizia: Optional[int]) -> str:
        payload = {
            "nome": nome,
            "modello": modello,
            "tipologia": tipologia,
            "sede": sede,
            "posizione": posizione,
            "intervallo_controllo_periodico": intervallo_controllo_periodico,
            "intervallo_pulizia": intervallo_pulizia,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        _, doc_ref = AssetService._collection.add(payload)
        return doc_ref.id

    @staticmethod
    def update(asset_id: str, data: dict) -> bool:
        payload = data.copy()
        payload.pop("id", None) 
        doc_ref = AssetService._collection.document(asset_id)
        try:
            doc_ref.update(payload)
            return True
        except Exception:
            return False

    @staticmethod
    def delete(asset_id: str) -> bool:
        parent_doc_ref = AssetService._collection.document(asset_id)
        subcollection_ref = parent_doc_ref.collection("interventi")

        try:
            while True:
                docs = subcollection_ref.limit(AssetService._BATCH_SIZE).stream()
                batch = db.batch()
                deleted_count = 0

                for doc in docs:
                    batch.delete(doc.reference)
                    deleted_count += 1

                if deleted_count == 0:
                    break

                batch.commit()
            parent_doc_ref.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_intervento(asset_id: str, intervento_id: str) -> dict | None:
        doc_ref = AssetService._collection.document(asset_id).collection("interventi").document(intervento_id)
        
        try:
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return None
            return {"id": snapshot.id, **snapshot.to_dict()}
        except Exception:
            return None
        
    @staticmethod
    def get_interventi(asset_id: str) -> list[dict]:
        docs = AssetService._collection.document(asset_id).collection("interventi").order_by("data", direction=firestore.Query.DESCENDING).stream()
        entries = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        entries.sort(key=lambda x: x.get("data", ""), reverse=True)
        return entries

    @staticmethod
    def add_intervento(asset_id: str, tipo: str, data: datetime, operatore: str, note: str, allegati: list[tuple[str, str]]) -> bool:
        try:
            AssetService._collection.document(asset_id).collection("interventi").add({
                "tipo": tipo,
                "data": data,
                "operatore": operatore,
                "note": note,
                "allegati": allegati
            })
            return True
        except Exception:
            return False

    @staticmethod
    def update_intervento(asset_id: str, intervento_id: str, tipo: Optional[str], data: Optional[datetime], operatore: Optional[str], note: Optional[str]) -> bool:
        doc_ref = AssetService._collection.document(asset_id).collection("interventi").document(intervento_id)
        try:
            update_data = {}
            if tipo is not None:
                update_data["tipo"] = tipo
            if data is not None:
                update_data["data"] = data
            if operatore is not None:
                update_data["operatore"] = operatore
            if note is not None:
                update_data["note"] = note
            doc_ref.update(update_data)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_intervento(asset_id: str, intervento_id: str) -> bool:
        doc_ref = AssetService._collection.document(asset_id).collection("interventi").document(intervento_id)
        try:
            doc_ref.delete()
            return True
        except Exception:
            return False