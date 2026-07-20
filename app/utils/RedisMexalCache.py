from datetime import timedelta
import json
import redis
from typing import Optional
from flask import current_app

class RedisMexalCache:
    def __init__(self):
        # Utilizza il connection pool nativo di redis-py per gestire i thread/worker
        # decode_responses=True evita di dover decodificare i byte-string a ogni fetch
        self.client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.ttl_aspetti = int(timedelta(hours=6).total_seconds())
        self.ttl_customers = int(timedelta(minutes=1).total_seconds())
        self.prefix_aspetti = "mx:aspetti:"
        self.prefix_customers = "mx:cust:"

    def get_aspetto_esteriore(self, mexal, codice: str) -> Optional[str]:
        key = f"{self.prefix_aspetti}{codice}"
        cached_val = self.client.get(key)

        if cached_val:
            return cached_val

        current_app.logger.warning(f"MX: Cache miss per aspetto codice: '{codice}'. Recupero da gestionale.")
        tutti_gli_aspetti = mexal.get_all_aspetti_esteriori_beni()

        # Pipeline per inviare le scritture in un singolo round-trip di rete
        pipeline = self.client.pipeline()
        for k, v in tutti_gli_aspetti.items():
            pipeline.setex(f"{self.prefix_aspetti}{k}", self.ttl_aspetti, v)
        pipeline.execute()

        return tutti_gli_aspetti.get(codice)

    def get_customers(self, mexal, codes: list[str]) -> dict:
        if not codes:
            return {}

        keys = [f"{self.prefix_customers}{c}" for c in codes]
        
        # MGET esegue il fetch di N chiavi in una singola operazione O(N)
        cached_vals = self.client.mget(keys)
        
        clienti = {}
        codici_da_richiedere = []

        # Zip accoppia il codice originale con il valore restituito da MGET (che può essere None)
        for cod, val in zip(codes, cached_vals):
            if val and False:
                clienti[cod] = json.loads(val)
            else:
                codici_da_richiedere.append(cod)

        if not codici_da_richiedere:
            return clienti

        current_app.logger.warning("MX: Cache miss per clienti. Richiesta al gestionale.")
        nuovi_clienti = mexal.find_customers(
            properties=["codice", "ragione_sociale",
                        "indirizzo", "cap", "localita", "provincia", "cod_paese",
                        "email", "telefono",
                        "denominazione", "gest_per_fisica"],
            filters=[("codice", "=", codici_da_richiedere)]
        )

        if nuovi_clienti:
            pipeline = self.client.pipeline()
            for cliente in nuovi_clienti:
                cod = cliente["codice"]
                clienti[cod] = cliente
                pipeline.setex(
                    f"{self.prefix_customers}{cod}",
                    self.ttl_customers,
                    json.dumps(cliente)
                )
            pipeline.execute()

        return clienti
    
    def remove_customer(self, cod_conto: str):
        self.client.delete(f"{self.prefix_customers}{cod_conto}")