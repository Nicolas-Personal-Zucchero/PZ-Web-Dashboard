REVIEW_EMAIL_OBJECT_ITA = "Ci farebbe piacere la tua opinione! 🌟"
REVIEW_EMAIL_OBJECT_ENG = "We’d love to hear your thoughts! 🌟"
AGENT_EMAIL_OBJECT_ITA = "Nuovo contatto assegnato"
CONTACT_EMAIL_OBJECT_ITA = "Grazie per il Suo Interesse – Il Nostro Consulente Locale La Contatterà"
CONTACT_EMAIL_OBJECT_ENG = "Thank You for Your Interest – Your Local Consultant Will Contact You"

REVIEW_EMAIL_BODY_ITA = """
Caro/a {customer},<br>
<br>
Speriamo che la tua esperienza con <b>Personal Zucchero</b> sia stata dolce quanto i nostri prodotti!<br>
Teniamo tantissimo al tuo parere e ci farebbe davvero piacere se volessi lasciarci una recensione su Google.<br>
<br>
👉 <b><a href="https://g.page/r/CVVzbjGLDF6kEAE/review">Lascia la tua recensione su Google:</a></b> <a href="https://g.page/r/CVVzbjGLDF6kEAE/review">https://g.page/r/CVVzbjGLDF6kEAE/review</a><br>
<br>
Bastano pochi secondi, ma per noi conta moltissimo!<br>
Puoi raccontare cosa ti è piaciuto di più:<br>
🍬 La qualità del prodotto acquistato<br>
🍭 La varietà di scelta tra i nostri prodotti personalizzati<br>
😊 La gentilezza e disponibilità del nostro staff<br>
📦 Il supporto ricevuto prima, durante o dopo l’acquisto<br>
<br>
Se hai avuto un momento speciale con noi, raccontacelo!<br>
La tua opinione aiuta anche altri a scegliere con fiducia.<br>
<br>
👉 <b><a href="https://g.page/r/CVVzbjGLDF6kEAE/review">Lascia la tua recensione su Google:</a></b> <a href="https://g.page/r/CVVzbjGLDF6kEAE/review">https://g.page/r/CVVzbjGLDF6kEAE/review</a><br>
<br>
Grazie di cuore per il tuo tempo e per aver scelto Personal Zucchero.<br>
A presto!<br>
<br>
{sender}<br>
"""

REVIEW_EMAIL_BODY_ENG = """
Dear {customer},<br>
<br>
We hope your experience with <b>Personal Zucchero</b> was as sweet as our treats!<br>
Your opinion means the world to us, and we’d truly appreciate it if you could leave us a review on Google.<br>
<br>
It only takes a few seconds, but it means a lot to us!<br>
You can share what you liked most:<br>
🍬 The quality of the product you purchased<br>
🍭 The variety of our personalized options<br>
😊 The kindness and helpfulness of our staff<br>
📦 The support you received before, during, or after your purchase<br>
<br>
If you had a special moment with us, we’d love to hear about it!<br>
Your feedback also helps others choose us with confidence.<br>
<br>
👉 <b><a href="https://g.page/r/CVVzbjGLDF6kEAE/review">Leave your review on Google:</a></b> <a href="https://g.page/r/CVVzbjGLDF6kEAE/review">https://g.page/r/CVVzbjGLDF6kEAE/review</a><br>
<br>
Thank you from the bottom of our hearts for your time and for choosing Personal Zucchero.<br>
See you soon!<br>
<br>
{sender}<br>
"""

AGENT_EMAIL_BODY_ITA = """
Ciao <b>{nome_agente}</b>,<br><br>

abbiamo un nuovo contatto da assegnarti. Qui di seguito trovi tutte le informazioni disponibili:<br><br>

Nome: <b>{nome_cliente}</b><br>
Cognome: <b>{cognome_cliente}</b><br>
Email: <b>{email_cliente}</b><br>
Telefono: <b>{telefono_cliente}</b><br>

Società: <b>{nome_azienda}</b><br>
Partita IVA: <b>{partita_iva}</b><br>
Categoria: <b>{categoria}</b><br>
Città: <b>{citta_azienda}</b><br>
Provincia: <b>{provincia_azienda}</b><br>
Prodotto di interesse: <b>{prodotto_di_interesse_azienda}</b><br>
Fonte del contatto: <b>{fonte_contatto}</b><br>
Note interne:<br>
{note_interne}<br><br>

Grazie e buon lavoro!<br><br>

Cordiali saluti,<br>
{mittente}
"""

CONTACT_EMAIL_BODY_ITA = """
Gentile <b>{nome_cliente}</b>,<br><br>

grazie per l'interesse dimostrato verso la nostra linea prodotti.<br><br>

Abbiamo già provveduto ad inoltrare il suo contatto al nostro consulente di zona, che provvederà a contattarla il prima possibile per darle assistenza in merito.<br>
Le anticipiamo i suoi contatti:<br><br>

Nome: <b>{nome_agente}</b><br>
Telefono: <b>{telefono_agente}</b><br>
Email: <b>{email_agente}</b><br><br>

Dalla nostra sede restiamo a disposizione per qualsiasi esigenza e con l'occasione anticipiamo il nostro catalogo prodotti per visionare tutte le nostre linee.<br><br>

Cordiali saluti,<br>
{mittente}
"""

CONTACT_EMAIL_BODY_ENG = """
Dear <b>{nome_cliente}</b>,<br><br>

Thank you for your interest in our product range.<br><br>

We have forwarded your contact details to our local consultant, who will get in touch with you shortly to provide assistance.<br>
In the meantime, here is their contact information:<br><br>

Name: <b>{nome_agente}</b><br>
Phone: <b>{telefono_agente}</b><br>
Email: <b>{email_agente}</b><br><br>

Our headquarters remain at your disposal for any further inquiries. Meanwhile, we are pleased to share our product catalog so you can explore all our offerings.<br><br>

Kind regards,<br>
{mittente}
"""

EMAIL_TEMPLATES = {
    "review_ita": {"object": REVIEW_EMAIL_OBJECT_ITA, "body": REVIEW_EMAIL_BODY_ITA},
    "review_eng": {"object": REVIEW_EMAIL_OBJECT_ENG, "body": REVIEW_EMAIL_BODY_ENG},
    "agent_ita": {"object": AGENT_EMAIL_OBJECT_ITA, "body": AGENT_EMAIL_BODY_ITA},
    "contact_ita": {"object": CONTACT_EMAIL_OBJECT_ITA, "body": CONTACT_EMAIL_BODY_ITA},
    "contact_eng": {"object": CONTACT_EMAIL_OBJECT_ENG, "body": CONTACT_EMAIL_BODY_ENG},
}