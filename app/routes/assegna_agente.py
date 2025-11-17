import os
from flask import Blueprint, render_template, request, redirect, flash, jsonify

from config.mail_config import EMAIL_TEMPLATES
from config.config import ITALY_TZ

from mailer_pz import MailerPZ
from utils.hubspot import HubspotPZ

from utils.firebase_client import db
from firebase_admin import firestore

assegna_agente_bp = Blueprint("assegna_agente", __name__, url_prefix="/assegna-agente")

assegnazione_contatti_agenti_collection = db.collection("assegnazione_contatti_agenti")

INFO_EMAIL_NAME = os.getenv("INFO_EMAIL_NAME", "")
INFO_EMAIL_ADDRESS = os.getenv("INFO_EMAIL_ADDRESS", "")
INFO_EMAIL_PASSWORD = os.getenv("INFO_EMAIL_PASSWORD", "")
HUBSPOT_AGENT_ASSIGNMENT_TOKEN = os.getenv("HUBSPOT_AGENT_ASSIGNMENT_TOKEN", "")

if not INFO_EMAIL_NAME:
    print("INFO_EMAIL_NAME is not set.")

if not INFO_EMAIL_ADDRESS:
    print("INFO_EMAIL_ADDRESS is not set.")

if not INFO_EMAIL_PASSWORD:
    print("INFO_EMAIL_PASSWORD is not set.")

if not HUBSPOT_AGENT_ASSIGNMENT_TOKEN:
    print("HUBSPOT_AGENT_ASSIGNMENT_TOKEN is not set.")

mailer = MailerPZ(INFO_EMAIL_NAME, INFO_EMAIL_ADDRESS, INFO_EMAIL_PASSWORD)
hubspot = HubspotPZ(HUBSPOT_AGENT_ASSIGNMENT_TOKEN)

@assegna_agente_bp.route("/get_contact")
def get_contact():
    email = request.args.get("email")    
    contact, company = get_contact_and_its_company(hubspot, email or "")
    return jsonify(
        contact=contact,
        company=company
    )
    
def get_field(form, key):
    value = form.get(key, "").strip()
    return value if value else None

@assegna_agente_bp.route("/", methods=["GET", "POST"])
def assegnaAgente():
    agents_by_id = get_active_agents_by_id(hubspot)
    contact_source_options = hubspot.getContactPropertyInfo("fonte").get("options", [])

    if request.method != "POST":
        return render_template("home/assegna-agente.html", agents=list(agents_by_id.values()), contact_source_options=contact_source_options)
    
    form = request.form

    sender = get_field(form, "nome_mittente")

    id_agente = get_field(form, "id_agente")
    agent = agents_by_id.get(id_agente)
    agent_note = get_field(form, "note_agente")
    lingua_email = get_field(form, "lingua_email")

    contact_info = {
        "email": get_field(form, "email"),
        "firstname": get_field(form, "nome_cliente"),
        "lastname": get_field(form, "cognome_cliente"),
        "phone": get_field(form, "telefono"),
        "fonte": get_field(form, "fonte"),
    }

    company_info = {
        "name": get_field(form, "societa"),
        "partita_iva": get_field(form, "partita_iva"),
        "categoria_mexal": get_field(form, "categoria_mexal"),
        "city": get_field(form, "citta"),
        "provincia": get_field(form, "provincia"),
        "prodotto_di_interesse": get_field(form, "prodotto_di_interesse"),
    }
    
    updated_contact, updated_company = upsert_contact_and_company(hubspot, contact_info, company_info)

    if not updated_contact or not updated_company:
        flash("Contatto o azienda non trovato in HubSpot. Chiedere a Nicolas", "danger")
        return redirect("/assegna-agente")

    add_assignment_to_firebase(agent, updated_contact, sender)

    send_agent_email(mailer, sender, agent, updated_contact, updated_company, agent_note)
    send_contact_email(mailer, sender, lingua_email, updated_contact, agent)

    associate_contact_agent(hubspot, updated_contact, agent)
    create_deal_for_agent(hubspot, agent, updated_contact)

    flash("Contatto assegnato all'agente con successo!", "success")
    return redirect("/assegna-agente")

def get_active_agents_by_id(hubspot):
    firebase_assignments = get_all_assignments()

    agents_ids = hubspot.getAgentsListMembersIds()
    agents = hubspot.getContactBatch(agents_ids, [
        "firstname", "lastname", "email", "phone", "mobilephone",
        "hs_additional_emails", "escluso_da_assegnazione_clienti"
    ])
    filtered_agents = [a for a in agents if a.get("escluso_da_assegnazione_clienti") == "false" and a.get("data_fine_contratto") == None]
    sorted_agents = sorted(filtered_agents, key=lambda a: ((a.get("lastname") or "zzzzzz").lower(), (a.get("firstname") or "").lower()))
    agents_by_id = {a['id']: a for a in sorted_agents}

    associations = hubspot.getContactsAssociatedContactsBatch(agents_ids)
    associated_contacts_ids = [item for sublist in associations.values() for item in sublist]
    associated_contacts = hubspot.getContactBatch(list(associated_contacts_ids), ["firstname", "lastname", "email"])
    associated_contacts_by_id = {c['id']: c for c in associated_contacts}

    for agent_id, contacts_ids in associations.items():
        if agent_id in agents_by_id: #Controllo non sia un agente escluso
            for contact_id in contacts_ids:
                for assignment in firebase_assignments:
                    if assignment["cliente"] == contact_id and assignment["agente"] == agent_id:
                        associated_contacts_by_id[contact_id]["operatore"] = assignment.get("operatore")
                        assigned_at = assignment.get("assigned_at")
                        if assigned_at:
                            local_time = assigned_at.astimezone(ITALY_TZ)
                            formatted_time = local_time.strftime("%d/%m/%Y, %H:%M:%S")
                        else:
                            formatted_time = "N/A"
                        associated_contacts_by_id[contact_id]["assigned_at"] = formatted_time
                        
            agents_by_id[agent_id]["associated_contacts"] = [associated_contacts_by_id[contact_id] for contact_id in contacts_ids]
    return agents_by_id

def validate_form_fields(form, required_fields):
    return all(form.get(f, "").strip() for f in required_fields)

def get_all_assignments():
    # Recupera tutti i documenti della collezione
    docs = assegnazione_contatti_agenti_collection.stream()
    all_assignments = []
    for doc in docs:
        data = doc.to_dict()
        # data["id"] = doc.id  # opzionale, aggiunge l'ID del documento
        all_assignments.append(data)
    return all_assignments

def add_assignment_to_firebase(agent, contact, sender):
    assegnazione_contatti_agenti_collection.add({
        "agente": agent["id"],
        "cliente": contact["id"],
        "operatore": sender,
        "assigned_at": firestore.SERVER_TIMESTAMP
    })

def get_first_company_id(contact):
    if not contact:
        return None
    
    associations = contact.get("associations", {})
    if associations == None:
        return None
    
    companies = associations.get("companies", {})

    if associations == None:
        return None
    
    results = companies.get("results", [])
    if not results:
        return None
    
    return results[0].get("id") #primo id della lista

def upsert_contact_and_company(hubspot, form_contact, form_company):
    #Rimuovo i campi valorizzati None (contact ha sicuramente email, company sicuramente name)
    form_contact = {k: v for k, v in form_contact.items() if v}
    form_company = {k: v for k, v in form_company.items() if v}

    hubspot_contact, hubspot_company = get_contact_and_its_company(hubspot, form_contact["email"])

    if hubspot_contact:
        #Aggiorna il contatto esistente.
        #Potrebbe essere stato selezionato manualmente ma il contatto esiste già su HubSpot
        hubspot.updateContact(hubspot_contact["id"], form_contact)
        contact_id = hubspot_contact["id"]
    else:
        contact_id = hubspot.createContact(form_contact)

    if contact_id and form_company != {}:
        if hubspot_company:
            hubspot.updateCompany(contact_id, form_company)
        else:
            company_id = hubspot.createCompany(form_company)
            if company_id:
                hubspot.createContactsAssociatedCompaniesBatch([(contact_id, company_id)])

    return get_contact_and_its_company(hubspot, form_contact["email"])

def send_agent_email(mailer, sender, agent, contact, company, note):
    mailer.invia_email_singola(
        destinatari=agent['email'],
        oggetto=EMAIL_TEMPLATES["agent_ita"]["object"],
        corpo=EMAIL_TEMPLATES["agent_ita"]["body"].format(
            nome_agente=agent.get("firstname") or "",

            nome_cliente=contact.get("firstname") or "",
            cognome_cliente=contact.get("lastname") or "",
            email_cliente=contact.get("email") or "",
            telefono_cliente=contact.get("phone") or "",

            nome_azienda=company.get("name") or "",
            partita_iva=company.get("partita_iva") or "",
            categoria=company.get("categoria_mexal") or "",
            citta_azienda=company.get("city") or "",
            provincia_azienda=company.get("provincia") or "",
            prodotto_di_interesse_azienda=company.get("prodotto_di_interesse") or "",
            fonte_contatto=contact.get("fonte") or "",

            note_interne=note,

            mittente=sender
        ),
        hubspot_ccn=True
    )

    mailer.invia_email_singola(
        destinatari="info@personalzucchero.com",
        oggetto=EMAIL_TEMPLATES["agent_ita"]["object"],
        corpo=EMAIL_TEMPLATES["agent_ita"]["body"].format(
            nome_agente=agent.get("firstname") or "",

            nome_cliente=contact.get("firstname") or "",
            cognome_cliente=contact.get("lastname") or "",
            email_cliente=contact.get("email") or "",
            telefono_cliente=contact.get("phone") or "",

            nome_azienda=company.get("name") or "",
            partita_iva=company.get("partita_iva") or "",
            categoria=company.get("categoria_mexal") or "",
            citta_azienda=company.get("city") or "",
            provincia_azienda=company.get("provincia") or "",
            prodotto_di_interesse_azienda=company.get("prodotto_di_interesse") or "",
            fonte_contatto=contact.get("fonte") or "",

            note_interne=note,

            mittente=sender
        ),
        hubspot_ccn=False
    )

def send_contact_email(mailer, sender, language, contact, agent):
    mailer.invia_email_singola(
        destinatari=contact["email"],
        oggetto=EMAIL_TEMPLATES["contact_" + language.lower()]["object"],
        corpo=EMAIL_TEMPLATES["contact_" + language.lower()]["body"].format(
            nome_cliente=contact.get("firstname") or "",
            nome_agente=f"{agent.get('firstname', '')} {agent.get('lastname', '')}",
            email_agente=agent.get("email") or "",
            telefono_agente=agent.get("phone", ""),
            cellulare_agente=agent.get("mobilephone", ""),
            mittente=sender
        ),
        hubspot_ccn=True
    )

def associate_contact_agent(hubspot, contact, agent):
    hubspot.createContactsAssociatedContactsBatch([(contact["id"], agent["id"])])

def create_deal_for_agent(hubspot, agent, contact):
    deal_id = hubspot.createAgentDeal({
        "dealname": f"Assegnazione contatto a {agent.get('lastname', '')} {agent.get('firstname', '')}",
        "dealstage": "3288687857",
    })
    hubspot.createContactsAssociatedDealsBatch([
        (deal_id, contact["id"]),
        (deal_id, agent["id"])
    ])

def get_contact_and_its_company(hubspot, email):
    contact = hubspot.getContactByEmail(email, hubspot._DEFAULT_CONTACT_PROPERTY_LIST)
    company_id = get_first_company_id(contact)
    company = hubspot.getCompany(company_id, ["name", "partita_iva", "categoria_mexal", "city", "provincia", "prodotto_di_interesse"]) if company_id else None
    return contact, company