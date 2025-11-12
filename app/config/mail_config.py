REVIEW_EMAIL_OBJECT_ITA = "Ci farebbe piacere la tua opinione! 🌟"
REVIEW_EMAIL_OBJECT_ENG = "We’d love to hear your thoughts! 🌟"
AGENT_EMAIL_OBJECT_ITA = "Nuovo contatto assegnato"
CONTACT_EMAIL_OBJECT_ITA = "Grazie per il Suo Interesse – Il Nostro Consulente Locale La Contatterà"
CONTACT_EMAIL_OBJECT_ENG = "Thank You for Your Interest – Our Local Consultant Will Contact You"

REVIEW_EMAIL_BODY_ITA = """
Caro/a {customer},<br>
<br>
Speriamo che la tua esperienza con Personal Zucchero sia stata dolce quanto i nostri prodotti!<br>
Teniamo tantissimo al tuo parere e ci farebbe davvero piacere se volessi lasciarci una recensione su Google, bastano davvero pochi secondi.<br>
<br>
Se hai avuto un momento speciale con noi, raccontacelo!<br>
La tua opinione aiuta anche altri a scegliere con fiducia.<br>
<br>
<!-- Pulsante "bulletproof" compatibile con la maggior parte dei client email -->
<!--[if mso]>
  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://g.page/r/CVVzbjGLDF6kEAE/review" style="height:44px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#d9534f">
    <w:anchorlock/>
    <center style="color:#ffffff;font-family:Arial, sans-serif;font-size:16px;font-weight:bold;">
      Valuta la tua esperienza
    </center>
  </v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left">
    <tr>
      <td align="center" bgcolor="#d9534f" style="border-radius:6px;">
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
If you had a special moment with us, we’d love to hear about it!<br>
Your opinion also helps others choose with confidence.<br>
<br>
<!-- "Bulletproof" button compatible with most email clients -->
<!--[if mso]>
  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://g.page/r/CVVzbjGLDF6kEAE/review" style="height:44px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#d9534f">
    <w:anchorlock/>
    <center style="color:#ffffff;font-family:Arial, sans-serif;font-size:16px;font-weight:bold;">
      Rate Your Experience
    </center>
  </v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left">
    <tr>
      <td align="center" bgcolor="#d9534f" style="border-radius:6px;">
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
<b>{note_interne}</b><br><br>

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
Email: <b>{email_agente}</b><br><br>

Our headquarters remain at your disposal for any further inquiries. Meanwhile, we are pleased to share our product catalog so you can explore all our offerings.<br><br>

<a href="https://personalzucchero.com/wp-content/uploads/2024/12/PZ_CAT_-2025-web.pdf" target="_blank">View Our Product Catalog</a><br><br>

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