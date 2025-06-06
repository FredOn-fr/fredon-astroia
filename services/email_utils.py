import os
import smtplib
from email.message import EmailMessage

def envoyer_conversation_par_mail(destinataire, nom, messages):
    import tempfile

    contenu_txt = ""
    for msg in messages:
        role = msg["role"].capitalize()
        texte = msg["content"].replace("\n", " ").strip()
        contenu_txt += f"{role} : {texte}\n\n"

    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.txt') as tmp:
        tmp.write(contenu_txt)
        chemin_fichier = tmp.name

    msg = EmailMessage()
    msg['Subject'] = f"[FredOn-AstroIA] Conversation avec {nom}"
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = destinataire
    msg.set_content(f"Voici l’historique de la conversation de {nom}, au format texte lisible.")

    with open(chemin_fichier, 'rb') as f:
        msg.add_attachment(f.read(), maintype='text', subtype='plain', filename=f"conversation_{nom}.txt")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        smtp.send_message(msg)

def envoyer_message_telegram(message):
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)
