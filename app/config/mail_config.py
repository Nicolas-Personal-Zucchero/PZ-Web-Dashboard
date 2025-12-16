REVIEW_EMAIL_OBJECT_ITA = "Ci farebbe piacere la tua opinione! 🌟"
REVIEW_EMAIL_OBJECT_ENG = "We’d love to hear your thoughts! 🌟"
AGENT_EMAIL_OBJECT_ITA = "Nuovo contatto assegnato {info_cliente}"
CONTACT_EMAIL_OBJECT_ITA = "Grazie per il Suo Interesse – Il Nostro Consulente Locale La Contatterà"
CONTACT_EMAIL_OBJECT_ENG = "Thank You for Your Interest – Our Local Consultant Will Contact You"
SIGEP_EMAIL_OBJECT_ITA = "Ecco i tuoi biglietti per il Sigep! 🎟️"
SIGEP_EMAIL_OBJECT_ENG = "Here are your Sigep tickets! 🎟️"

REVIEW_EMAIL_BODY_ITA = """
Caro/a {customer},<br>
<br>
Speriamo che la tua esperienza con Personal Zucchero sia stata dolce quanto i nostri prodotti!<br>
Teniamo tantissimo al tuo parere e ci farebbe davvero piacere se volessi lasciarci una recensione su Google, bastano davvero pochi secondi.<br>
<br>
<b>La tua opinione ci aiuta</b> e permette anche altri di scegliere con fiducia.<br>
<br>
<!-- Pulsante "bulletproof" compatibile con la maggior parte dei client email -->
<!--[if mso]>
  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://g.page/r/CVVzbjGLDF6kEAE/review" style="height:44px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#00a6e2">
    <w:anchorlock/>
    <center style="color:#ffffff;font-family:Arial, sans-serif;font-size:16px;font-weight:bold;">
      Valuta la tua esperienza
    </center>
  </v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left">
    <tr>
      <td align="center" bgcolor="#00a6e2" style="border-radius:6px;">
        <a href="https://g.page/r/CVVzbjGLDF6kEAE/review"
           target="_blank"
           style="display:inline-block;padding:12px 24px;font-family:Arial, sans-serif;font-size:16px;color:#ffffff;text-decoration:none;font-weight:bold;border-radius:6px;"
           role="button"
           aria-label="Valuta la tua esperienza">
          Valuta la tua esperienza
        </a>
      </td>
    </tr>
  </table>
<!--<![endif]-->
<br>
<br>
<br>
Grazie di cuore per il tuo tempo e per aver scelto Personal Zucchero.<br>
A presto!<br>
<br>
{sender}<br>
"""

REVIEW_EMAIL_BODY_ENG = """
Dear {customer},<br>
<br>
We hope your experience with Personal Zucchero was as sweet as our products!<br>
We truly value your feedback and would greatly appreciate it if you could take a few seconds to leave us a review on Google.<br>
<br>
<b>Your feedback helps us</b> and allows others to choose with confidence.<br>
<br>
<!-- "Bulletproof" button compatible with most email clients -->
<!--[if mso]>
  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://g.page/r/CVVzbjGLDF6kEAE/review" style="height:44px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#00a6e2">
    <w:anchorlock/>
    <center style="color:#ffffff;font-family:Arial, sans-serif;font-size:16px;font-weight:bold;">
      Rate Your Experience
    </center>
  </v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left">
    <tr>
      <td align="center" bgcolor="#00a6e2" style="border-radius:6px;">
        <a href="https://g.page/r/CVVzbjGLDF6kEAE/review"
           target="_blank"
           style="display:inline-block;padding:12px 24px;font-family:Arial, sans-serif;font-size:16px;color:#ffffff;text-decoration:none;font-weight:bold;border-radius:6px;"
           role="button"
           aria-label="Rate Your Experience">
          Rate Your Experience
        </a>
      </td>
    </tr>
  </table>
<!--<![endif]-->
<br>
<br>
<br>
Thank you sincerely for your time and for choosing Personal Zucchero.<br>
We hope to see you again soon!<br>
<br>
{sender}<br>
"""

AGENT_EMAIL_BODY_ITA = """
Ciao <b>{nome_agente}</b>,<br>
<br>
abbiamo un nuovo contatto da assegnarti. Qui di seguito trovi tutte le informazioni disponibili:<br>
<br>
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
<br>
Note interne:<br>
<b>{note_interne}</b><br>
<br>
{informazioni_logo}
<br>
<span style="background-color: yellow;">Fonte del contatto: <b>{fonte_contatto}</b></span><br>
<br>
<span style="color: red; font-weight: bold;">ATTENZIONE: È strettamente necessario indicare la "Fonte del contatto" (sopra evidenziata) al momento della trasmissione dell’ordine al nostro ufficio ordini.</span><br>
<br>
Grazie e buon lavoro!<br>
<br>
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
Cellulare: <b>{cellulare_agente}</b><br>
Email: <b>{email_agente}</b><br><br>

Dalla nostra sede restiamo a disposizione per qualsiasi esigenza e con l'occasione anticipiamo il nostro catalogo prodotti per visionare tutte le nostre linee.<br><br>

<a href="https://personalzucchero.com/wp-content/uploads/2024/12/PZ_CAT_-2025-web.pdf" target="_blank">Visualizza il nostro catalogo prodotti</a><br><br>

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
Mobile: <b>{cellulare_agente}</b><br>
Email: <b>{email_agente}</b><br><br>

Our headquarters remain at your disposal for any further inquiries. Meanwhile, we are pleased to share our product catalog so you can explore all our offerings.<br><br>

<a href="https://personalzucchero.com/wp-content/uploads/2024/12/PZ_CAT_-2025-web.pdf" target="_blank">View Our Product Catalog</a><br><br>

Kind regards,<br>
{mittente}
"""

SIGEP_EMAIL_BODY_ITA = """
Gentile {nome_cliente},<br>
<br>
Siamo lieti di invitarti a <b>Sigep 2026</b>! Abbiamo riservato per te dei codici promozionali che ti permetteranno di acquistare il biglietto d'ingresso giornaliero al prezzo ridotto di <b>€ 10,00</b> (anziché € 75,00).<br>
<br>
Ecco i tuoi codici sconto (un codice per ogni ingresso):<br>
<b>{codici_biglietti}</b><br>
<br>
<b>COME ATTIVARE I CODICI:</b><br>
<br>
1. <b>Registrati:</b> Se non lo hai già fatto, crea un account visitatore su questa pagina:<br>
<a href="https://www.sigep.it/it/reserved-area/user/registration">https://www.sigep.it/it/reserved-area/user/registration</a><br>
(Dopo l'iscrizione, riceverai una mail per confermare e completare la registrazione).<br>
<br>
2. <b>Accedi alla biglietteria:</b> Una volta registrato, vai alla sezione Ticket qui:<br>
<a href="https://www.sigep.it/it/reserved-area/tickets">https://visita.sigep.it/reserved-area/ticket</a><br>
<br>
3. <b>Inserisci il codice:</b> Inserisci il codice fornito sopra e clicca su <b>"Attiva"</b>, poi clicca su <b>"Gestisci"</b> e procedi con il pagamento ridotto seguendo le istruzioni della pagina.<br>
<br>
Nell'attesa di incontrarci in fiera, ti invitiamo a scoprire in anteprima la nostra gamma completa di prodotti scaricando il <b>Catalogo 2025</b>:<br>
👉 <a href="https://personalzucchero.com/wp-content/uploads/2024/12/PZ_CAT_-2025-web.pdf">Clicca qui per scaricare il catalogo</a><br>
<br>
Ti aspettiamo al nostro stand!<br>
📍 <b>Padiglione A4 – Stand 029</b><br>
<br>
Per qualsiasi dubbio sulla procedura, non esitare a contattarci.<br>
<br>
Cordiali saluti,<br>
<b>Personal Zucchero</b>"""

SIGEP_EMAIL_BODY_ENG = """
Dear {nome_cliente},<br>
<br>
We are pleased to invite you to <b>Sigep 2026</b>! We have reserved special promotional codes for you, allowing you to purchase a daily entrance ticket for just <b>€10.00</b> (instead of €75.00).<br>
<br>
Here are your discount codes (each code is valid for one daily admission):<br>
<b>{codici_biglietti}</b><br>
<br>
<b>HOW TO REDEEM YOUR CODE:</b><br>
<br>
1. <b>Register:</b> First, enter your details and create a visitor account here:<br>
<a href="https://www.sigep.it/en/reserved-area/user/registration">https://www.sigep.it/en/reserved-area/user/registration</a><br>
(You will receive a confirmation email to finalize your registration).<br>
<br>
2. <b>Go to Tickets:</b> Once registered, access the Ticket section here:<br>
<a href="https://www.sigep.it/en/reserved-area/tickets">https://www.sigep.it/en/reserved-area/tickets</a><br>
<br>
3. <b>Enter the Code:</b> Enter the code provided above, then click on <b>"Activate"</b>, then click on <b>"Manage"</b> and follow the instructions to complete the reduced payment.<br>
<br>
In the meantime, we invite you to discover our complete range of products by downloading our <b>2025 Catalogue</b>:<br>
👉 <a href="https://personalzucchero.com/wp-content/uploads/2024/12/PZ_CAT_-2025-web.pdf">Click here to download the catalogue</a><br>
<br>
We look forward to seeing you there!<br>
📍 <b>Hall A4 – Stand 029</b><br>
<br>
Should you have any questions, please do not hesitate to contact us.<br>
<br>
Best regards,<br>
<b>Personal Zucchero</b>"""

EMAIL_TEMPLATES = {
    "review_ita": {"object": REVIEW_EMAIL_OBJECT_ITA, "body": REVIEW_EMAIL_BODY_ITA},
    "review_eng": {"object": REVIEW_EMAIL_OBJECT_ENG, "body": REVIEW_EMAIL_BODY_ENG},
    "agent_ita": {"object": AGENT_EMAIL_OBJECT_ITA, "body": AGENT_EMAIL_BODY_ITA},
    "contact_ita": {"object": CONTACT_EMAIL_OBJECT_ITA, "body": CONTACT_EMAIL_BODY_ITA},
    "contact_eng": {"object": CONTACT_EMAIL_OBJECT_ENG, "body": CONTACT_EMAIL_BODY_ENG},
    "sigep_ita": {"object": SIGEP_EMAIL_OBJECT_ITA, "body": SIGEP_EMAIL_BODY_ITA},
    "sigep_eng": {"object": SIGEP_EMAIL_OBJECT_ENG, "body": SIGEP_EMAIL_BODY_ENG}
}