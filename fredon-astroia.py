

import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import smtplib
from email.message import EmailMessage

# === CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("ASTROLOGYAPI_USER_ID")
API_KEY = os.getenv("ASTROLOGYAPI_API_KEY")

st.set_page_config(page_title="FredOn-AstroIA", layout="centered")
st.title("🔮 FredOn-AstroIA : Thème natal astrologique")

# === FONCTIONS ===

def get_coords_from_google(city_name):
    import os
    # Google Maps
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city_name, "key": os.getenv("GOOGLE_MAPS_API_KEY")}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("results")
        if results:
            loc = results[0]["geometry"]["location"]
            name = results[0]["formatted_address"]
            return loc["lat"], loc["lng"], name

    # Fallback LocationIQ
    locationiq_key = os.getenv("LOCATIONIQ_KEY")
    if locationiq_key:
        locationiq_url = "https://eu1.locationiq.com/v1/search.php"
        l_params = {
            "key": locationiq_key,
            "q": city_name,
            "format": "json",
            "limit": 1
        }
        l_headers = {"User-Agent": "fredon-astroia"}
        l_response = requests.get(locationiq_url, params=l_params, headers=l_headers)
        if l_response.status_code == 200:
            l_data = l_response.json()[0]
            return float(l_data["lat"]), float(l_data["lon"]), l_data["display_name"]

    return None, None, None

def get_timezone(lat, lon, year, month, day):
    url = "https://json.astrologyapi.com/v1/timezone_with_dst"
    data = {"latitude": lat, "longitude": lon, "date": f"{year}-{month:02d}-{day:02d}"}
    response = requests.post(url, auth=HTTPBasicAuth(USER_ID, API_KEY), json=data)
    if response.status_code == 200:
        return float(response.json()["timezone"])
    return 1.0

def generer_fichier_html(nom, resume, planetes, interpretation, chart_url):
    contenu_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                color: #333;
            }}
            h1, h2 {{
                color: #4a148c;
            }}
            img {{
                width: 100%;
                max-width: 400px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Thème natal de {nom}</h1>
        <p><strong>Résumé :</strong> {resume}</p>
        <h2>🖼️ Carte du ciel</h2>
        <img src="{chart_url}" alt="Carte du ciel">
        <h2>🪐 Positions des planètes</h2>
        <ul>
            {''.join(f"<li>{p}</li>" for p in planetes)}
        </ul>
        <h2>✨ Interprétation poétique</h2>
        <p>{interpretation.replace('\n', '<br>')}</p>
    </body>
    </html>
    """
    chemin_html = f"theme_{nom}.html"
    with open(chemin_html, "w", encoding="utf-8") as f:
        f.write(contenu_html)
    return chemin_html

def envoyer_email(destinataire, chemin_html, nom):
    msg = EmailMessage()
    msg['Subject'] = f"Ton thème natal - {nom}"
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = destinataire
    msg.set_content(f"Bonjour {nom},\n\nVoici ton thème astrologique en pièce jointe. 🌌")

    with open(chemin_html, 'rb') as f:
        msg.add_attachment(f.read(), maintype='text', subtype='html', filename=f"theme_{nom}.html")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        smtp.send_message(msg)

traductions = {
    "Sun": "Soleil", "Moon": "Lune", "Mercury": "Mercure", "Venus": "Vénus", "Mars": "Mars",
    "Jupiter": "Jupiter", "Saturn": "Saturne", "Uranus": "Uranus", "Neptune": "Neptune", "Pluto": "Pluton",
    "North Node": "Nœud Nord", "South Node": "Nœud Sud",
    "Aries": "Bélier", "Taurus": "Taureau", "Gemini": "Gémeaux", "Cancer": "Cancer",
    "Leo": "Lion", "Virgo": "Vierge", "Libra": "Balance", "Scorpio": "Scorpion",
    "Sagittarius": "Sagittaire", "Capricorn": "Capricorne", "Aquarius": "Verseau", "Pisces": "Poissons"
}

# === SAISIE ===

nom = st.text_input("Ton prénom ou pseudo")
col1, col2, col3 = st.columns(3)
with col1:
    day = st.number_input("Jour", 1, 31, 1)
with col2:
    month = st.number_input("Mois", 1, 12, 1)
with col3:
    year = st.number_input("Année", 1900, 2100, 1990)
col4, col5 = st.columns(2)
with col4:
    hour = st.number_input("Heure", 0, 23, 12)
with col5:
    minute = st.number_input("Minute", 0, 59, 0)
ville = st.text_input("Ville de naissance")
if not ville:
    st.warning("✋ Merci d’entrer une ville avec pays, ex : Paris, France")

lat, lon, location_name = get_coords_from_google(ville)
if lat is None or lon is None:
    st.error("Ville introuvable.")
else:
    tzone = get_timezone(lat, lon, year, month, day)
    st.success(f"📍 Localisation : {location_name}")
    st.write(f"🌐 Lat : {lat}, Lon : {lon} | UTC{tzone:+.1f}")

    birth_data = {
        "day": int(day), "month": int(month), "year": int(year),
        "hour": int(hour), "min": int(minute),
        "lat": lat, "lon": lon, "tzone": tzone
    }

    if st.button("🎁 Générer mon thème complet"):
     with st.spinner("🔮 Génération de votre thème en cours..."):
        auth = HTTPBasicAuth(USER_ID, API_KEY)
        base_url = "https://json.astrologyapi.com/v1/"

        chart = requests.post(base_url + "natal_wheel_chart", auth=auth, json=birth_data)
        if chart.status_code == 200:
            st.session_state["chart_url"] = chart.json()["chart_url"]

        planets = requests.post(base_url + "planets/tropical", auth=auth, json={**birth_data, "hsys": "placidus"})
        planet_lines = []
        if planets.status_code == 200:
            for p in planets.json():
                name = traductions.get(p["name"], p["name"])
                sign = traductions.get(p["sign"], p["sign"])
                house = p.get("house", "?")
                planet_lines.append(f"{name} en {sign}, maison {house}")
            st.session_state["planet_lines"] = planet_lines

            resume_theme = f"Voici le thème natal de {nom}, né le {day}/{month}/{year} à {hour:02d}:{minute:02d} à {location_name}."
            resume_theme += " Planètes : " + ", ".join(planet_lines) + "."

            prompt = resume_theme + " Fais une interprétation astrologique poétique, bienveillante et inspirante de ce thème."
            interpretation = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Tu es un astrologue poétique et bienveillant."},
                    {"role": "user", "content": prompt}
                ]
            ).choices[0].message.content

            st.session_state["resume_theme"] = resume_theme
            st.session_state["interpretation"] = interpretation
            st.session_state["chat_messages"] = [
                {"role": "system", "content": "Tu es un astrologue poétique et bienveillant."},
                {"role": "user", "content": resume_theme},
                {"role": "assistant", "content": interpretation}
            ]

            st.success("✨ Thème généré avec succès ! Découvre ton interprétation ci-dessous.")

# ✅ Affichage persistant si thème généré

if all(k in st.session_state for k in ("resume_theme", "planet_lines", "interpretation", "chart_url")):
    chemin_html = generer_fichier_html(
        nom,
        st.session_state["resume_theme"],
        st.session_state["planet_lines"],
        st.session_state["interpretation"],
        st.session_state["chart_url"]
    )

    with open(chemin_html, "rb") as file:
        st.download_button(
            label="📥 Télécharger mon thème en HTML",
            data=file,
            file_name=f"theme_{nom}.html",
            mime="text/html"
        )

    email_user = st.text_input("📨 Entre ton adresse e-mail pour recevoir ton thème")
    if st.button("Envoyer mon thème par mail") and email_user:
        envoyer_email(email_user, chemin_html, nom)
        st.success("✅ Ton thème a été envoyé par e-mail avec succès !")

# === AFFICHAGE PERSISTANT

if "chart_url" in st.session_state:
    st.subheader("🖼️ Carte du ciel")
    st.image(st.session_state["chart_url"])

if "planet_lines" in st.session_state:
    st.subheader("🌟 Positions des planètes (signes et maisons)")
    for line in st.session_state["planet_lines"]:
        st.write(f"🪐 {line}")

if "interpretation" in st.session_state:
    st.subheader("✨ Interprétation poétique (IA)")
    st.write(st.session_state["interpretation"])

# === CHATBOT AVEC GPT-3.5

if "chat_messages" in st.session_state:
    st.markdown("---")
    st.subheader("💬 Discute avec Astro-IA")

    for msg in st.session_state.chat_messages[3:]:
        role = "Toi" if msg["role"] == "user" else "Astro-IA"
        st.markdown(f"**{role} :** {msg['content']}")

    user_input = st.text_input("Pose une nouvelle question à Astro-IA", key="new_chat_input")
    if st.button("Envoyer ma question"):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        chat_reply = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.chat_messages
        )
        msg = chat_reply.choices[0].message.content
        st.session_state.chat_messages.append({"role": "assistant", "content": msg})
        st.rerun()
