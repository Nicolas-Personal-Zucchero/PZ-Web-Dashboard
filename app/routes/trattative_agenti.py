from flask import Blueprint, render_template
from config.config import ITALY_TZ
from config.secrets_manager import secrets_manager
from datetime import datetime

trattative_agenti_bp = Blueprint("trattative_agenti", __name__, url_prefix="/trattative_agenti")

@trattative_agenti_bp.route("/", methods=["GET", "POST"])
def index():
    hubspot = secrets_manager.get_hubspot()

    #Prendo i nomi delle fasi della pipeline agenti
    pipeline_info = hubspot.getPipelineInfo("deals", hubspot._AGENT_PIPELINE_ID)
    stages_by_id = {stage["id"]: stage for stage in pipeline_info.get("stages", [])}

    # Prendo tutte le trattative
    deals = hubspot.getAllDeals(hubspot._AGENT_DEAL_PROPERTY_LIST) or []

    # Prendo le trattative della pipeline agenti
    deals = [t for t in deals if t.get("pipeline", "") == hubspot._AGENT_PIPELINE_ID]

    # Prendo le trattative non chiuse
    temp = []
    for t in deals:
        probability = stages_by_id.get(t.get("dealstage"), {}).get("metadata", {}).get("probability", 0.5)
        if probability == 0.0 or probability == 1.0:
            continue
        temp.append(t)
    deals = temp

    # Prendo le trattative più vecchie di DAYS giorni
    DAYS = 30
    thirty_days_ago = datetime.now(ITALY_TZ).timestamp() - (DAYS * 24 * 60 * 60)

    temp = []
    for t in deals:
        t["dealstage"] = stages_by_id.get(t.get("dealstage"), {}).get("label", t.get("dealstage"))
        createdate = t.get("createdate")
        if createdate:
            createdate_dt = datetime.fromisoformat(createdate).astimezone(ITALY_TZ)
            if createdate_dt.timestamp() < thirty_days_ago:
                t["createdate"] = createdate_dt.strftime("%d/%m/%Y")
                temp.append(t)
        else:
            t["createdate"] = "N/A"
    deals = temp

    #Prendo tutti i contatti e le aziende associate
    contacts_ids = set()
    companies_ids = set()
    for deal in deals:
        associations = deal.get("associations", {})

        contact_info = associations.get("contacts", {}).get("results", [])
        company_info = associations.get("companies", {}).get("results", [])
        
        contact_ids = {c.get("id") for c in contact_info if c.get("id")}
        company_ids = {c.get("id") for c in company_info if c.get("id")}

        contacts_ids.update(contact_ids)
        companies_ids.update(company_ids)
    
    return render_template("/trattative_agenti.html", trattative=deals)