#pip install .
from typing import Optional, Dict, List, Tuple, Any
import requests
from datetime import datetime

class HubspotPZ:
    _BASER_URL = "https://api.hubapi.com"
    _MAX_BATCH_SIZE = 100
    _DEFAULT_CONTACT_PROPERTY_LIST = ["email","firstname","lastname","phone","mobilephone","numero_referente","hs_additional_emails", "fonte"]
    _DEFAULT_AGENT_PROPERTY_LIST = ["codice_mexal", "nome_mexal", "frequenza_liquidazione", "ruolo", "address", "cap", "city", "provincia", "data_inizio_contratto", "data_fine_contratto", "tipologia_contratto", "regione", "province", "note_zona", "dettagli_particolare"]
    _DEFAULT_COMPANY_PROPERTY_LIST = ['codice_mexal','name','alias','partita_iva','categoria_mexal','segmento','city','provincia','region','paese','lingua','data_ultima_fattura','hs_country_code','stagionalita__cloned_','precancellata']
    _DEFAULT_DEAL_PROPERTY_LIST =["dealname", "dealstage", "nome_cliente", "preventivo_confermato", "bozza_confermata"]
    _AGENT_LIST_ID = 67
    _AGENT_CONTACTS_LIST_ID = 64

    def __init__(self, token: str) -> None:
        self._initializeHubspotHeaders(token)

    def _initializeHubspotHeaders(self, token: str) -> None:
        self._headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }

    def _convertiData(self, timeMillisecond: str) -> Optional[datetime.date]:
        if timeMillisecond == "":
            return None
        millisecond = int(timeMillisecond)
        timestamp = millisecond / 1000  # Converti millisecondi in secondi dividendo per 1000
        data = datetime.fromtimestamp(timestamp)
        return data.date()

    ##########Properties############################################

    def _getPropertyInfo(self, object_type: str, property_name: str) -> Any:
        endpoint = self._BASER_URL + f'/crm/v3/properties/{object_type}/{property_name}'
        r = requests.get(url=endpoint, headers=self._headers)
        
        if r.status_code != 200:
            print(f"Error {r.status_code} during the retrieval of a property information on HubSpot.\nResponse Body: {r.text}")
            return None
        return r.json()

    def getContactPropertyInfo(self, property_name: str) -> Any:
        return self._getPropertyInfo("contacts", property_name)
    
    def getCompanyPropertyInfo(self, property_name: str) -> Any:
        return self._getPropertyInfo("companies", property_name)
    
    ##########All Objects############################################

    #Tested and working
    def _getAllObjects(
        self,
        object_type: str,
        properties_names: List[str],
        associations_objects: Optional[List[str]] = None,
        accumulated_objects: Optional[List[Dict[str, str]]] = None,
        after: str = None
    ) -> List[Dict[str, str]]:
        """
        Funzione generica per ottenere tutti gli oggetti di un certo tipo (contatti, aziende, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipi degli oggetti (ad esempio 'contacts' o 'companies')
        :param properties_names: Lista di proprietà da ottenere per ogni oggetto
        :param accumulated_objects: Lista di oggetti accumulati durante le chiamate ricorsive
        :return: Lista degli oggetti richiesti
        """
        if accumulated_objects is None:
            accumulated_objects = []

        params_list = [f"properties={prop}" for prop in properties_names]
        if associations_objects is not None:
            params_list.append(f"associations={','.join(associations_objects)}")
        if after:
            params_list.insert(0, f"after={after}")
        params = "&".join(params_list)

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}?limit=100&{params}'

        r = requests.get(url=endpoint, headers=self._headers)

        if r.status_code != 200:
            print(f"Error {r.status_code} during the retrieval of all contacts.\nResponse Body: {r.text}")
            return None
        
        for result in r.json().get("results", []):
            retrieved_properties = {prop: result.get("properties", {}).get(prop) or None for prop in properties_names}
            retrieved_properties["id"] = result.get("id")
            retrieved_properties = dict(sorted(retrieved_properties.items()))
            retrieved_properties["associations"] = result.get("associations", None)
            accumulated_objects.append(retrieved_properties)

        next_page = r.json().get("paging", {}).get("next", {}).get("after")
        if next_page:
            return self._getAllObjects(object_type, properties_names, associations_objects, accumulated_objects, next_page)

        return accumulated_objects
    
    def getAllContacts(self, properties_names: List[str]) -> List[Dict[str, str]]:
        return self._getAllObjects("contacts", properties_names, associations_objects=["companies"])
    
    def getAllCompanies(self, properties_names: List[str]) -> List[Dict[str, str]]:
        return self._getAllObjects("companies", properties_names, associations_objects=["contacts"])
    
    ##########Single Objects############################################
    
    #Tested and working
    def _createObject(
        self,
        object_type: str,
        properties: Dict[str, str]
    ) -> Optional[str]:
        """
        Funzione generica per creare un oggetto (contatto, azienda, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo dell'oggetto (ad esempio 'contacts' o 'companies')
        :param kwargs: Proprietà dell'oggetto da creare
        :return: ID dell'oggetto creato, oppure None in caso di errore
        """

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}'
        r = requests.post(url=endpoint, headers=self._headers, json={ "properties": properties })
        
        if r.status_code != 201:
            print(f"Error {r.status_code} during the creation of an object on HubSpot.\nResponse Body: {r.text}")
            return None
        
        return r.json().get("id", None)  # Usa .get per evitare KeyError se l'ID non esiste

    #Tested and working
    def _archiveObject(
        self,
        object_type: str,
        object_id: str
    ) -> bool:
        """
        Funzione generica per archiviare un oggetto (contatto, azienda, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo dell'oggetto (ad esempio 'contacts' o 'companies')
        :param object_id: ID dell'oggetto da archiviare
        :return: True se archiviato correttamente, False altrimenti
        """

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/{object_id}'
        r = requests.delete(url=endpoint, headers=self._headers)
        
        if r.status_code != 204:
            print(f"Error {r.status_code} during the archivation of an object on HubSpot.\nResponse Body: {r.text}")
            return False
        
        return True
    
    #Tested and working
    def _updateObject(
        self,
        object_type: str,
        object_id: str,
        properties: Dict[str, str]
    ) -> bool:
        """
        Funzione generica per aggiornare un oggetto (contatto, azienda, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo dell'oggetto (ad esempio 'contacts' o 'companies')
        :param object_id: ID dell'oggetto da aggiornare
        :param kwargs: Proprietà dell'oggetto da aggiornare
        :return: True se aggiornato correttamente, False altrimenti
        """

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/{object_id}'
        r = requests.patch(url=endpoint, headers=self._headers, json={ "properties": properties })
        
        if r.status_code != 200:
            print(f"Error {r.status_code} during the update of an object on HubSpot.\nResponse Body: {r.text}")
            return False
        
        return True  # Usa .get per evitare KeyError se l'ID non esiste
    
    #Tested and working
    def _getObject(
        self,
        object_type: str,
        object_id: str,
        properties_names: List[str],
        identifying_property: str = "id",
        associations_objects: Optional[List[str]] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Funzione generica per ottenere un oggetto (contatto, azienda, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo dell'oggetto (ad esempio 'contacts' o 'companies')
        :param object_id: ID dell'oggetto da ottenere (l'identificatore può essere qualsiasi campo univoco, come l'email, si passa il nome del campo in identifying_property)
        :param properties_names: Proprietà dell'oggetto da ottenere
        :return: Un dizionario con le proprietà dell'oggetto richieste, oppure None in caso di errore
        """

        params_list = [f"properties={prop}" for prop in properties_names]
        if identifying_property != "id":
            params_list.insert(0, f"idProperty={identifying_property}")

        if associations_objects is not None:
            params_list.append(f"associations={','.join(associations_objects)}")

        params = "&".join(params_list)
        
        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/{object_id}?{params}'
        r = requests.get(url=endpoint, headers=self._headers)
        
        if r.status_code != 200:
            print(f"Error {r.status_code} during the update of an object on HubSpot.\nResponse Body: {r.text}")
            return None
        
        retrieved_properties = {prop: r.json().get("properties", {}).get(prop) or None for prop in properties_names}
        retrieved_properties["id"] = r.json().get("id")
        retrieved_properties["associations"] = r.json().get("associations", None)
        return dict(sorted(retrieved_properties.items()))

    #Tested and working
    def _searchObject(
        self,
        object_type: str,
        search_params: Dict[str, str],
        properties_names: List[str]
    ) -> Optional[Dict[str, str]]:
        """
        Funzione generica per cercare un oggetto (contatto, azienda, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo dell'oggetto (ad esempio 'contacts' o 'companies')
        :search_params: Le proprietà con i valori su cui filtrare la ricerca
        :param properties_names: Proprietà dell'oggetto da ottenere
        :return: Un dizionario con le proprietà dell'oggetto richieste, oppure None in caso di errore
        """
        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/search'
        r = requests.post(url=endpoint, headers=self._headers,
                         json={"properties": properties_names,
                               "filterGroups":[
                                   {"filters": [ 
                                       {"propertyName": name, "operator": "EQ", "value": value } for name, value in search_params.items()
                                       ]}]})
        
        if r.status_code != 200:
            print(f"Error {r.status_code} during the search of an object on HubSpot.\nResponse Body: {r.text}")
            return None
        
        output = []
        for result in r.json().get("results", []):
            retrieved_properties = {prop: result.get("properties").get(prop) for prop in properties_names}
            retrieved_properties["id"] = result.get("id")
            output.append(retrieved_properties)
        return output
    
    #Tested and working
    def createContact(self, properties: Dict[str, str]) -> Optional[str]:
        return self._createObject("contacts", properties)

    #Tested and working
    def createCompany(self, properties: Dict[str, str]) -> Optional[str]:
        return self._createObject("companies", properties)
    
    #Tested and working
    def archiveContact(self, contact_id: str) -> bool:
        return self._archiveObject("contacts", contact_id)

    #Tested and working
    def archiveCompany(self, company_id: str) -> bool:
        return self._archiveObject("companies", company_id)

    #Tested and working
    def updateContact(self, contact_id: str, properties: Dict[str, str]) -> bool:
        return self._updateObject("contacts", contact_id, properties)
    
    #Tested and working
    def updateCompany(self, company_id: str, properties: Dict[str, str]) -> bool:
        return self._updateObject("companies", company_id, properties)
    
    #Tested and working
    def getContact(self, contact_id: str, properties_names: List[str] = []) -> Optional[Dict[str, str]]:
        return self._getObject("contacts", contact_id, properties_names, associations_objects=["companies"])

    #Tested and working
    def getContactByEmail(self, contact_email: str, properties_names: List[str] = []) -> Optional[Dict[str, str]]:
        return self._getObject("contacts", contact_email, properties_names, "email", associations_objects=["companies"])
    
    #Tested and working
    def getCompany(self, company_id: str, properties_names: List[str] = []) -> Optional[Dict[str, str]]:
        return self._getObject("companies", company_id, properties_names, associations_objects=["contacts"])
    
    def getContactSecondaryEmails(self, contact_id: str) -> List[str]:
        endpoint = self._BASER_URL + f"/contacts/v1/secondary-email/{contact_id}"
        r = requests.get(url=endpoint, headers=self._headers)
        return r.json()['secondaryEmails'] if len(r.json()['secondaryEmails']) > 0 else []
    
    def createAgentDeal(self, properties: Dict[str, str]) -> Optional[str]:
        #https://app-eu1.hubspot.com/property-settings/25378285/properties?type=0-3&eschref=%2Fcontacts%2F25378285%2Fobjects%2F0-3%2Frestore&search=pip&action=edit&property=pipeline
        properties["pipeline"] = "2405411057"
        return self._createObject("deals", properties)
    
    def createContactDeal(self, properties: Dict[str, str]) -> Optional[str]:
        #https://app-eu1.hubspot.com/property-settings/25378285/properties?type=0-3&eschref=%2Fcontacts%2F25378285%2Fobjects%2F0-3%2Frestore&search=pip&action=edit&property=pipeline
        properties["pipeline"] = "59157733"
        return self._createObject("deals", properties)
    
    ##########Objects Batch############################################

    def _createObjectBatch(
        self,
        object_type: str,
        properties_list: List[Dict[str, str]],
        accumulated_ids: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """
        Funzione generica per creare un batch di oggetti (contatti, aziende, ecc.) su HubSpot.
        Versione API V3.
        In questa prima implementazione non sto gestendo le associazioni, batch create di SOLO oggetti senza relazioni
        
        :param object_type: Tipi dell'oggetto (ad esempio 'contacts' o 'companies')
        :param properties_list: Lista di proprietà
        :param accumulated_ids: Lista di ID accumulati durante le chiamate ricorsive
        :return: Lista di ID degli oggetti creati, oppure None in caso di errore
        """

        if accumulated_ids is None:
            accumulated_ids = []

        # Caso ricorsivo base: se la lista è vuota, restituisci gli ID accumulati
        if not properties_list:
            return accumulated_ids if accumulated_ids else None

        # Prendi il massimo numero di elementi
        batch = properties_list[:self._MAX_BATCH_SIZE]
        remaining = properties_list[self._MAX_BATCH_SIZE:]

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/batch/create'
        r = requests.post(url=endpoint,
                          headers=self._headers,
                          json={ "inputs": [{"properties": properties} for properties in batch] })

        if r.status_code != 201:
            #Status code 207 è un codice strano, multi-status. Credo significhi che qualche oggetto ha dato errore e qualche no
            print(f"Error {r.status_code} during the creation of a batch of objects on HubSpot.\nResponse Body: {r.text}")
            # return None
        else:
            results = r.json().get("results", [])
            accumulated_ids.extend([result.get("id") for result in results if result.get("id")])
        
        return self._createObjectBatch(object_type, remaining, accumulated_ids)

    def _archiveObjectBatch(
        self,
        object_type: str,
        id_list: List[str]
    ) -> bool:
        """
        Funzione generica per archiviare un batch di oggetti (contatti, aziende, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo degli oggetti (ad esempio 'contacts' o 'companies')
        :param id_list: Lista di id da archiviare
        :return: True se archiviati correttamente, False altrimenti
        """

        # Caso ricorsivo base: se la lista è vuota, restituisci True
        if not id_list:
            return True

        # Prendi il massimo numero di elementi
        batch = id_list[:self._MAX_BATCH_SIZE]
        remaining = id_list[self._MAX_BATCH_SIZE:]
        
        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/batch/archive'
        r = requests.post(url=endpoint,
                          headers=self._headers,
                          json={ "inputs": [{"id": id} for id in batch] })

        if r.status_code != 204:
            print(f"Error {r.status_code} during the archivation of a batch of objects on HubSpot.\nResponse Body: {r.text}")
            return False
        
        return self._archiveObjectBatch(object_type, remaining)
        
    def _updateObjectBatch(
        self,
        object_type: str,
        id_to_properties_list: Dict[str, Dict[str, str]]
    ) -> bool:
        """
        Funzione generica per aggiornare un batch di oggetti (contatti, aziende, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipi dell'oggetto (ad esempio 'contacts' o 'companies')
        :param id_to_properties_list: Dizionario che mappa ID degli oggetti al dizionario di proprietà da aggiornare
        :return: True se aggiornato correttamente, False altrimenti
        """

        # Caso ricorsivo base: se il dizionario è vuoto, restituisci True
        if not id_to_properties_list:
            return True
        
        # Prendi il massimo numero di elementi
        batch = dict(list(id_to_properties_list.items())[:self._MAX_BATCH_SIZE]) #Primi MAX_BATCH_SIZE elementi
        remaining = dict(list(id_to_properties_list.items())[self._MAX_BATCH_SIZE:]) #Elementi rimanenti
        
        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/batch/update'
        r = requests.post(url=endpoint,
                          headers=self._headers,
                          json={ "inputs": [{"id": id, "properties": properties} for id, properties in batch.items()] })

        if r.status_code != 200:
            #Status code 207 è un codice strano, multi-status. Credo significhi che qualche oggetto ha dato errore e qualche no
            print(f"Error {r.status_code} during the update of a batch of objects on HubSpot.\nResponse Body: {r.text}")
            return False
        
        return self._updateObjectBatch(object_type, remaining)

    def _getObjectBatch(
        self,
        object_type: str,
        id_list: List[str],
        properties_names: List[str],
        accumulated_objects: Optional[List[Dict[str, str]]] = None
    ) -> Optional[List[Dict[str, str]]]:
        """
        Funzione generica per ottenere un batch di oggetti (contatti, aziende, ecc.) su HubSpot.
        Versione API V3.
        
        :param object_type: Tipo degli oggetti (ad esempio 'contacts' o 'companies')
        :param id_list: Lista di id da ottenere
        :properties_names: Lista di proprietà da ottenere
        :return: Lista di dizionari con le proprietà degli oggetti richiesti, oppure None in caso di errore
        """

        if accumulated_objects is None:
            accumulated_objects = []

        # Caso ricorsivo base: se la lista è vuota, restituisci gli oggetti accumulati
        if not id_list:
            return accumulated_objects if accumulated_objects else None
        
        # Prendi il massimo numero di elementi
        batch = id_list[:self._MAX_BATCH_SIZE]
        remaining = id_list[self._MAX_BATCH_SIZE:]

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/batch/read'
        r = requests.post(url=endpoint,
                          headers=self._headers,
                          json={ "inputs": [{"id": id} for id in batch], "properties": properties_names })

        if r.status_code != 200:
            print(f"Error {r.status_code} during the retrieval of a batch of objects on HubSpot.\nResponse Body: {r.text}")
            return None
        
        output = []
        for result in r.json().get("results", []):
            retrieved_properties = {prop: result.get("properties", {}).get(prop) or None for prop in properties_names}
            retrieved_properties["id"] = result.get("id")
            retrieved_properties = dict(sorted(retrieved_properties.items()))
            output.append(retrieved_properties)
        accumulated_objects.extend(output)
        
        return self._getObjectBatch(object_type, remaining, properties_names, accumulated_objects)
     
    def createContactBatch(self, properties_list: List[Dict[str, str]]) -> Optional[List[str]]:
        return self._createObjectBatch("contacts", properties_list)

    def createCompanyBatch(self, properties_list: List[Dict[str, str]]) -> Optional[List[str]]:
        return self._createObjectBatch("companies", properties_list)
    
    def archiveContactBatch(self, id_list: List[str]) -> bool:
        return self._archiveObjectBatch("contacts", id_list)

    def archiveCompanyBatch(self, id_list: List[str]) -> bool:
        return self._archiveObjectBatch("companies", id_list)
    
    def updateContactBatch(self, id_to_properties_list: Dict[str, Dict[str, str]]) -> bool:
        return self._updateObjectBatch("contacts", id_to_properties_list)

    def updateCompanyBatch(self, id_to_properties_list: Dict[str, Dict[str, str]]) -> bool:
        return self._updateObjectBatch("companies", id_to_properties_list)
    
    def getContactBatch(self, id_list: List[str], properties_names: List[str]) -> Optional[List[Dict[str, str]]]:
        return self._getObjectBatch("contacts", id_list, properties_names)

    def getCompanyBatch(self, id_list: List[str], properties_names: List[str]) -> Optional[List[Dict[str, str]]]:
        return self._getObjectBatch("companies", id_list, properties_names)

    ##########Lists############################################

    #Tested and working
    def getListMembersIds(
        self,
        list_id: str,
        accumulated_ids: Optional[List[str]] = None,
        after: str = None
    ) -> Optional[List[str]]:
        """
        Funzione generica per ottenere i contatti facenti parte di una lista su HubSpot.
        Versione API V3.
        
        :param list_id: ID della lista da cui ottenere i membri
        :properties_names: Lista di proprietà da ottenere per ogni membro
        :return: Lista di id dei membri del gruppo, oppure None in caso di errore
        """
        if accumulated_ids is None:
            accumulated_ids = []
        
        endpoint = self._BASER_URL + f'/crm/v3/lists/{list_id}/memberships?limit=250'
        if after:
            endpoint += f"&after={after}"

        r = requests.get(url=endpoint, headers=self._headers)

        if r.status_code != 200:
            print(f"Error {r.status_code} during the retrieval of the members of a list.\nResponse Body: {r.text}")
            return None
        
        ids = [result.get("recordId") for result in r.json().get("results", []) if "recordId" in result]
        accumulated_ids.extend(ids)
        next_page = r.json().get("paging", {}).get("next", {}).get("after")
        if next_page:
            return self.getListMembersIds(list_id, accumulated_ids, next_page)

        return accumulated_ids

    #Tested and working
    def getAgentsListMembersIds(self) -> Optional[List[str]]:
        return self.getListMembersIds(self._AGENT_LIST_ID)
    
    ##########Associations############################################

    def _getObjectAssociations(
        self,
        from_object_type: str,
        to_object_type: str,
        from_object_id: str
    ) -> Optional[List[str]]:
        """
        Funzione generica per ottenere le associazioni di un oggetto su HubSpot.
        Non ho implementato le chiamate ricorsive in quanto, essendo il limite a 500 associazioni, non dovrebbe mai essere necessario.
        Versione API V4.

        :param from_object_type: Tipo dell'oggetto di partenza
        :param to_object_type: Tipo dell'oggetto di arrivo
        :param from_object_id: ID dell'oggetto di partenza
        :return: Lista di ID degli oggetti associati, oppure None in caso di errore
        """

        endpoint = self._BASER_URL + f"/crm/v4/objects/{from_object_type}/{from_object_id}/associations/{to_object_type}"

        r = requests.get(url=endpoint, headers=self._headers)
        if r.status_code != 200:
            print(f"Error {r.status_code} during the retrieval of associations between objects.\nResponse Body: {r.text}")
            return None

        toIds = [to["to"]["toObjectId"] for to in r.json().get("results", [])]
        return toIds
    
    def getContactAssociatedCompanies(self, contact_id: str) -> Optional[List[str]]:
        return self._getObjectAssociations("contacts", "companies", contact_id)

    def getCompanyAssociatedContacts(self, company_id: str) -> Optional[List[str]]:
        return self._getObjectAssociations("companies", "contacts", company_id)
    
    ##########Associations Batch############################################

    def _getObjectAssociationsBatch(
        self,
        from_object_type: str,
        to_object_type: str,
        from_object_ids: List[str],
        accumulated_associations: Optional[Dict[str, List[str]]] = None
    ) -> Optional[Dict[str, List[str]]]:
        """
        Funzione generica per ottenere le associazioni di molteplici oggetti su HubSpot.
        Versione API V4.

        :param from_object_type: Tipo dell'oggetto di partenza
        :param to_object_type: Tipo dell'oggetto di arrivo
        :param from_object_id: Lista degli ID degli oggetti di partenza
        :return: Mappa di ID degli oggetti di partenza a liste di ID degli oggetti associati, oppure None in caso di errore
        """

        if accumulated_associations is None:
            accumulated_associations = {}

        # Caso ricorsivo base: se la lista è vuota, restituisci gli oggetti accumulati
        if not from_object_ids:
            return accumulated_associations if accumulated_associations else None
        
        # Prendi il massimo numero di elementi
        batch = from_object_ids[:self._MAX_BATCH_SIZE]
        remaining = from_object_ids[self._MAX_BATCH_SIZE:]

        endpoint = self._BASER_URL + f"/crm/v4/associations/{from_object_type}/{to_object_type}/batch/read"
        
        for toId in batch:
            #aggiungi la chiave se non presente (con valore lista vuota)
            accumulated_associations.setdefault(toId, [])
        
        # Prepara il payload per la richiesta
        r = requests.post(url=endpoint, headers=self._headers, json={ "inputs": [{"id": id} for id in batch] })

        if r.status_code != 200 and r.status_code != 207:
            print(f"Error {r.status_code} during the retrieval in batch of associations between objects.\nResponse Body: {r.text}")
            return None
        
        for result in r.json().get("results", []):
            fromId = str(result.get("from").get("id"))
            toids = [str(to["toObjectId"]) for to in result.get("to", [])]
            accumulated_associations[fromId] = toids

        return self._getObjectAssociationsBatch(from_object_type, to_object_type, remaining, accumulated_associations)
    
    def _createObjectAssociationsBatch(
        self,
        from_object_type: str,
        to_object_type: str,
        associations: List[Tuple[str, str]]
    ) -> bool:
        
        """
        Funzione generica per creare le associazioni di molteplici oggetti su HubSpot.
        Versione API V4.

        :param from_object_type: Tipo degli oggetti di partenza
        :param to_object_type: Tipo degli oggetto di arrivo
        :param associations: Lista di tuple (toId, fromId) che rappresentano le associazioni da creare
        :return: True se tutto è andato a buon fine, False altrimenti
        """

        # Caso ricorsivo base: se la lista è vuota, restituisci True
        if not associations:
            return True

        endpoint = self._BASER_URL + f"/crm/v4/associations/{from_object_type}/{to_object_type}/batch/associate/default"
        
        batch = associations[:self._MAX_BATCH_SIZE]
        remaining = associations[self._MAX_BATCH_SIZE:]

        r = requests.post(url=endpoint, headers=self._headers, json={ "inputs": [{"from": {"id": toId}, "to": {"id": fromId}} for toId, fromId in batch] })

        if r.status_code != 200:
            print(f"Error {r.status_code} during the creation in batch of associations between objects.\nResponse Body: {r.text}")
            return False
        
        return self._createObjectAssociationsBatch(from_object_type, to_object_type, remaining)

    def _archiveObjectAssociationsBatch(
        self,
        from_object_type: str,
        to_object_type: str,
        associations: List[Tuple[str, List[str]]]
    ) -> bool:
        """
        Funzione generica per archiviare le associazioni di molteplici oggetti su HubSpot.
        Versione API V4.

        :param from_object_type: Tipo degli oggetti di partenza
        :param to_object_type: Tipo degli oggetto di arrivo
        :param associations: Lista di tuple di (toId, fromIds) che rappresentano le associazioni da archiviare
        :return: True se tutto è andato a buon fine, False altrimenti
        """

        # Caso ricorsivo base: se la lista è vuota, restituisci True
        if not associations:
            return True

        endpoint = self._BASER_URL + f"/crm/v4/associations/{from_object_type}/{to_object_type}/batch/archive"
        
        batch = associations[:self._MAX_BATCH_SIZE]
        remaining = associations[self._MAX_BATCH_SIZE:]

        r = requests.post(url=endpoint, headers=self._headers, json={ "inputs": [{"from": {"id": toId}, "to": [{"id": fromId} for fromId in fromIds]} for toId, fromIds in batch] })

        if r.status_code != 204:
            print(f"Error {r.status_code} during the archivation in batch of associations between objects.\nResponse Body: {r.text}")
            return False
        
        return self._archiveObjectAssociationsBatch(from_object_type, to_object_type, remaining)
    
    def getContactsAssociatedCompaniesBatch(self, contacts_ids: List[str]) -> Optional[Dict[str, List[str]]]:
        return self._getObjectAssociationsBatch("contacts", "companies", contacts_ids)
    
    def getCompaniesAssociatedContactsBatch(self, companies_ids: List[str]) -> Optional[Dict[str, List[str]]]:
        return self._getObjectAssociationsBatch("companies", "contacts", companies_ids)
    
    def getContactsAssociatedContactsBatch(self, contacts_ids: List[str]) -> Optional[Dict[str, List[str]]]:
        return self._getObjectAssociationsBatch("contacts", "contacts", contacts_ids)

    def createContactsAssociatedCompaniesBatch(self, associations: List[Tuple[str, str]]) -> bool:
        return self._createObjectAssociationsBatch("contacts", "companies", associations)
    
    def archiveContactsAssociatedCompaniesBatch(self, associations: List[Tuple[str, str]]) -> bool:
        return self._archiveObjectAssociationsBatch("contacts", "companies", associations)
    
    def createContactsAssociatedContactsBatch(self, associations: List[Tuple[str, str]]) -> bool:
        return self._createObjectAssociationsBatch("contacts", "contacts", associations)
    
    def createContactsAssociatedDealsBatch(self, associations: List[Tuple[str, str]]) -> bool:
        return self._createObjectAssociationsBatch("deals", "contacts", associations)

    ##########Actions############################################

    def _mergeObjects(
        self,
        object_type: str,
        main_object_id: str,
        object_to_merge_id: str
    ) -> bool:
        """
        Funzione per unire due aziende su HubSpot.
        Versione API V3.
        
        :param main_company_id: ID dell'azienda principale
        :param company_to_merge_id: ID dell'azienda da unire
        :return: True se unite correttamente, False altrimenti
        """

        endpoint = self._BASER_URL + f'/crm/v3/objects/{object_type}/merge'

        r = requests.post(url=endpoint, headers=self._headers, json={ "objectIdToMerge": object_to_merge_id, "primaryObjectId": main_object_id })

        if r.status_code != 200:
            print(f"Error {r.status_code} during the merge of objects {object_type} on HubSpot.\nResponse Body: {r.text}")
            return False
        
        return True
    
    def mergeCompanies(self, main_company_id: str, company_to_merge_id: str) -> bool:
        return self._mergeObjects("companies", main_company_id, company_to_merge_id)
    
    def mergeContacts(self, main_contact_id: str, contact_to_merge_id: str) -> bool:
        return self._mergeObjects("contacts", main_contact_id, contact_to_merge_id)
    