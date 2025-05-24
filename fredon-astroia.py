

import streamlit as st
st.set_page_config(page_title="FredOn-AstroIA", layout="centered")

for key in ["resume_theme", "planet_lines", "aspects_lines", "interpretation", "chart_url", "chat_messages"]:
    if key not in st.session_state:
        st.session_state[key] = None

honeypot_placeholder = st.empty()  # conteneur vide

with honeypot_placeholder.container():
    honey = st.text_input(" ", key="honey", label_visibility="collapsed")

# Après 100 ms, on vide le bloc (il disparaît sans laisser de trace)
import time
time.sleep(0.1)
honeypot_placeholder.empty()

if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

st.markdown("""
    <style>
        /* Titres H1 à H3 en violet avec effet */
        h1, h2, h3 {
            color: #5E4AE3 !important;
            font-family: 'Segoe UI', sans-serif;
            text-shadow: 1px 1px 2px rgba(94, 74, 227, 0.3);
            transition: all 0.3s ease;
        }

        h1:hover, h2:hover, h3:hover {
            text-shadow: 2px 2px 4px rgba(94, 74, 227, 0.5);
            transform: scale(1.01);
        }

        /* Optionnel : changer les boutons aussi */
        .stButton > button {
            background-color: #0C0C2C;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            transition: 0.2s;
        }

        .stButton > button:hover {
            background-color: #0C0C2C;
            transform: scale(1.02);
        }
   
        div.honeypot {
            display: none !important;
        }

        /* Ne cache que les messages des st.text_input */
        div[data-baseweb="form-control"] input + div[role="alert"] {
            display: none !important;
        }

    </style>
            
""", unsafe_allow_html=True)

tabs = st.tabs(["Thème natal", "Synastrie 🔧", "Transits 🔧"])

with tabs[0]:
    st.markdown("🧬 **Bienvenue dans l’analyse de ton thème natal**")

    import requests
    import openai
    import os
    import time
    from dotenv import load_dotenv
    from requests.auth import HTTPBasicAuth
    import smtplib
    from email.message import EmailMessage

    # === CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ===
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    USER_ID = os.getenv("ASTROLOGYAPI_USER_ID")
    API_KEY = os.getenv("ASTROLOGYAPI_API_KEY")

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

    import io

    def generer_fichier_html(nom, resume, planetes, aspects, interpretation, chart_url):
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
            <h2>🪐 Aspects planétaires</h2>
            <ul>
                {''.join(f"<li>{a}</li>" for a in aspects)}
            </ul>

            <h2>✨ Interprétation poétique</h2>
            <p>{interpretation.replace('\n', '<br>')}</p>
        </body>
        </html>
        """
        return contenu_html

    def generer_discussion_html(nom, messages):
        contenu_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; }}
                .assistant {{ color: #4a148c; margin-bottom: 10px; }}
                .user {{ color: #00695c; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>💬 Discussion avec Astro-IA de {nom}</h1>
        """
        for msg in messages[3:]:
            role = "assistant" if msg["role"] == "assistant" else "user"
            label = "Astro-IA" if role == "assistant" else "Toi"
            contenu_html += f'<p class="{role}"><strong>{label} :</strong> {msg["content"].replace("\n", "<br>")}</p>'
        contenu_html += "</body></html>"

        return contenu_html

    def detect_aspect(angle_diff):
        aspects = {
            "conjonction": (0, 8),
            "sextile": (60, 6),
            "carré": (90, 6),
            "trigone": (120, 6),
            "opposition": (180, 8)
        }
        for name, (angle, orbe) in aspects.items():
            diff = abs(angle_diff - angle)
            if diff <= orbe or abs(360 - angle_diff - angle) <= orbe:
                return name, round(diff, 1)
        return None, None

    signs = ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"]

    def get_longitude(degree, minute, sign):
        try:
            index = signs.index(sign)
            return index * 30 + degree + minute / 60
        except:
            return None

    traductions = {
        "Sun": "Soleil", "Moon": "Lune", "Mercury": "Mercure", "Venus": "Vénus", "Mars": "Mars",
        "Jupiter": "Jupiter", "Saturn": "Saturne", "Uranus": "Uranus", "Neptune": "Neptune", "Pluto": "Pluton",
        "North Node": "Nœud Nord", "South Node": "Nœud Sud", "Midheaven": "Milieu du Ciel",
        "Aries": "Bélier", "Taurus": "Taureau", "Gemini": "Gémeaux", "Cancer": "Cancer",
        "Leo": "Lion", "Virgo": "Vierge", "Libra": "Balance", "Scorpio": "Scorpion",
        "Sagittarius": "Sagittaire", "Capricorn": "Capricorne", "Aquarius": "Verseau", "Pisces": "Poissons"
    }

    traductions_aspects = {
        "conjunction": "conjonction",
        "sextile": "sextile",
        "square": "carré",
        "trine": "trigone",
        "opposition": "opposition",
        "quincunx": "quinconce",
        "semisextile": "semi-sextile",
        "semisquare": "semi-carré",
        "sesquiquadrate": "sesquicarré",
        "quintile": "quintile",
        "biquintile": "biquintile"
    }

    def envoyer_conversation_par_mail(destinataire, nom, messages):
        import tempfile
        from email.message import EmailMessage

        # Créer contenu .txt lisible
        contenu_txt = ""
        for msg in messages:
            role = msg["role"].capitalize()
            texte = msg["content"].replace("\n", " ").strip()
            contenu_txt += f"{role} : {texte}\n\n"

        # Sauvegarde temporaire du fichier .txt
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.txt') as tmp:
            tmp.write(contenu_txt)
            chemin_fichier = tmp.name

        # Préparer le mail
        msg = EmailMessage()
        msg['Subject'] = f"[FredOn-AstroIA] Conversation avec {nom}"
        msg['From'] = os.getenv("SMTP_USER")
        msg['To'] = destinataire
        msg.set_content(f"Voici l’historique de la conversation de {nom}, au format texte lisible.")

        # Ajouter la pièce jointe .txt
        with open(chemin_fichier, 'rb') as f:
            msg.add_attachment(f.read(), maintype='text', subtype='plain', filename=f"conversation_{nom}.txt")

        # Envoi SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            smtp.send_message(msg)

    # === SAISIE ===
        
    with st.form("form_theme"):
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
        lat = lon = location_name = None
        if ville.strip():
            lat, lon, location_name = get_coords_from_google(ville)
            if lat and lon:
                st.success(f"📍 Localisation trouvée : {location_name}")
                st.write(f"🌐 Latitude : {lat}, Longitude : {lon}")
            else:
                st.error("❌ Ville introuvable ou mal orthographiée.")
        style_ia = st.radio(
            "Quel style d'interprétation astrologique souhaites-tu ?",
            ["🌙 Poétique et inspirante", "🧠 Classique et analytique"],
            index=0
            )
        submitted = st.form_submit_button("🎁 Générer mon thème complet")

    lat = lon = location_name = None
    if ville.strip():
        lat, lon, location_name = get_coords_from_google(ville)
        if lat and lon:
            if not submitted:
                st.success(f"📍 Localisation trouvée : {location_name}")
                st.write(f"🌐 Latitude : {lat}, Longitude : {lon}")
        else:
            st.error("❌ Ville introuvable ou mal orthographiée.")

    # === Génération du thème uniquement si ville trouvée et bouton cliqué ===
    if submitted:
        if honey.strip() != "":
            st.error("🚫 Accès refusé. Suspicion de robot.")
        elif time.time() - st.session_state["start_time"] < 2:
            st.warning("⏱️ Tu vas trop vite. Attends quelques secondes.")
        elif not lat or not lon:
            st.error("❌ Impossible de générer le thème sans une ville valide.")
        else:
            tzone = get_timezone(lat, lon, year, month, day)
            st.write(f"🌐 Lat : {lat}, Lon : {lon} | UTC{tzone:+.1f}")

            birth_data = {
                "day": int(day), "month": int(month), "year": int(year),
                "hour": int(hour), "min": int(minute),
                "lat": lat, "lon": lon, "tzone": tzone
            }

            if submitted:
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

                    # ➤ Récupération des aspects avec western_horoscope
                    western = requests.post(base_url + "western_horoscope", auth=auth, json=birth_data)
                    aspects_lines = []
                    if western.status_code == 200:
                        horoscope_data = western.json()

                        aspects = horoscope_data.get("aspects", [])
                        for asp in aspects:
                            planets = asp.get("planets", ["?", "?"])
                            if len(planets) == 2:
                                planet1 = traductions.get(asp.get("aspecting_planet", "?"), asp.get("aspecting_planet", "?"))
                                planet2 = traductions.get(asp.get("aspected_planet", "?"), asp.get("aspected_planet", "?"))
                                aspect_type_en = str(asp.get("type", "aspect inconnu")).lower()
                                aspect_type = traductions_aspects.get(aspect_type_en, aspect_type_en)
                                orb = asp.get("orb", "?")
                                aspects_lines.append(f"{planet1} {aspect_type} {planet2} (orbe {orb:.1f}°)")
                            else:
                                st.warning(f"Aspects mal formé : {asp}")

                        st.session_state["aspects_lines"] = aspects_lines

                        resume_theme = f"Voici le thème natal de {nom}, né le {day}/{month}/{year} à {hour:02d}:{minute:02d} à {location_name}."
                        resume_theme += " Planètes : " + ", ".join(planet_lines) + "."
                        resume_theme += " Aspects : " + ", ".join(aspects_lines) + "."


                        if style_ia == "🌙 Poétique et inspirante":
                            system_prompt = "Tu es un astrologue poétique et bienveillant. Tu ne réponds pas à des questions sur le thème du suicide, de la mort ou de la drogue. Si l'utilisateur présente des difficultés psychologiques ou maladives, le diriger vers les instances médicales compétentes...."
                            user_prompt = resume_theme + " Fais une interprétation astrologique poétique, bienveillante et inspirante de ce thème."
                        else:
                            system_prompt = "Tu es un astrologue classique, rigoureux et pédagogue.Tu ne réponds pas à des questions sur le thème du suicide, de la mort ou de la drogue. Si l'utilisateur présente des difficultés psychologiques ou maladives, le diriger vers les instances médicales compétentes."
                            user_prompt = resume_theme + " Donne une interprétation astrologique classique, structurée et précise de ce thème."

                        interpretation = openai.chat.completions.create(
                            model="gpt-4-turbo",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ]
                        ).choices[0].message.content

                        st.session_state["resume_theme"] = resume_theme
                        st.session_state["interpretation"] = interpretation
                        st.session_state["chat_messages"] = [
                            {"role": "system", "content": "Tu es un astrologue poétique et bienveillant, tu connais le thème astral de l'utilisateur. Tu ne réponds pas à des questions sur le thème du suicide, de la mort ou de la drogue. Si l'utilisateur présente des difficultés psychologiques ou maladives, le diriger vers les instances médicales compétentes."},
                            {"role": "user", "content": resume_theme},
                            {"role": "assistant", "content": interpretation}
                        ]
                    

                        st.success("✨ Thème généré avec succès ! Découvre ton interprétation ci-dessous.")
                
    # ✅ Affichage persistant si thème généré

    import io

    # ✅ Vérification avant d'utiliser les clés de session_state
    if all(k in st.session_state and st.session_state[k] is not None for k in ("resume_theme", "planet_lines", "aspects_lines", "interpretation", "chart_url")):
        contenu_html = generer_fichier_html(
            nom,
            st.session_state["resume_theme"],
            st.session_state["planet_lines"],
            st.session_state["aspects_lines"],
            st.session_state["interpretation"],
            st.session_state["chart_url"]
        )

        st.download_button(
            label="📥 Télécharger mon thème en HTML",
            data=contenu_html,
            file_name=f"theme_{nom}.html",
            mime="text/html"
        )

    # === AFFICHAGE PERSISTANT

    if "chart_url" in st.session_state and st.session_state["chart_url"]:
        st.subheader("🖼️ Carte du ciel")
        st.image(st.session_state["chart_url"])

    if "planet_lines" in st.session_state and st.session_state["planet_lines"]:
        st.subheader("🌟 Positions des planètes (signes et maisons)")
        for line in st.session_state["planet_lines"]:
            st.write(f"🪐 {line}")

    if "aspects_lines" in st.session_state and st.session_state["aspects_lines"]:
        st.subheader("🪐 Aspects planétaires")
        for line in st.session_state["aspects_lines"]:
            st.write(f"🔹 {line}")

    if "interpretation" in st.session_state and st.session_state["interpretation"]:
        if style_ia == "🌙 Poétique et inspirante":
            st.subheader("✨ Interprétation poétique (IA)")
        else:
            st.subheader("🧠 Interprétation classique (IA)")
        
        st.write(st.session_state["interpretation"])

    # === CHATBOT AVEC GPT-3.5 ===
    if "chat_messages" in st.session_state and isinstance(st.session_state["chat_messages"], list):
        st.markdown("---")
        st.subheader("💬 Discute avec Astro-IA")

        for msg in st.session_state["chat_messages"][3:]:
            role = "Toi" if msg["role"] == "user" else "Astro-IA"
            st.markdown(f"**{role} :** {msg['content']}")

        user_input = st.text_input("Pose une nouvelle question à Astro-IA", key="new_chat_input")
        if st.button("Envoyer ma question") and user_input.strip():
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})

            try:
                chat_reply = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state["chat_messages"]
                )
                msg = chat_reply.choices[0].message.content
                st.session_state["chat_messages"].append({"role": "assistant", "content": msg})

                if nom:
                    envoyer_conversation_par_mail("fredon.fr@gmail.com", nom, st.session_state["chat_messages"])

            except Exception as e:
                st.error(f"Erreur lors de la réponse de l'IA : {e}")

            st.rerun()

        # 🔽 Export discussion
        if st.session_state["chat_messages"]:
            html_discussion = generer_discussion_html(nom, st.session_state["chat_messages"])

            st.download_button(
                label="📥 Télécharger la discussion avec Astro-IA",
                data=html_discussion,
                file_name=f"discussion_{nom}.html",
                mime="text/html"
            )

with tabs[1]:  # Synastrie
    st.header("💞 Synastrie (en construction)")
    st.info("🔧 La fonctionnalité de synastrie (comparaison entre deux thèmes) est en cours de développement. Reviens bientôt !")

with tabs[2]:  # Transits
    st.header("🌠 Transits astrologiques (en construction)")
    st.info("🔧 Cette section te permettra bientôt d'explorer les transits jour par jour. Patience cosmique… 🌌")


    import datetime

    st.markdown("---")
    st.subheader("🌠 Explorer les transits astrologiques")

    date_transit = st.date_input("Choisis une date pour explorer les transits", value=datetime.date.today())

    if st.button("✨ Analyse astrologique des transits (avec API)") and all(k in st.session_state for k in ("planet_lines", "resume_theme")):
        with st.spinner("🔭 Lecture astrologique des transits en cours..."):

            base_url = "https://json.astrologyapi.com/v1/"
            auth = HTTPBasicAuth(USER_ID, API_KEY)

            transit_payload = {
                "birth_date": f"{birth_data['year']:04d}-{birth_data['month']:02d}-{birth_data['day']:02d}",
                "birth_time": f"{birth_data['hour']:02d}:{birth_data['min']:02d}",
                "birth_lat": birth_data["lat"],
                "birth_lon": birth_data["lon"],
                "timezone": birth_data["tzone"],
                "transit_date": date_transit.strftime("%Y-%m-%d")
            }

            response = requests.post(base_url + "natal_transits/daily", auth=auth, json=transit_payload)

            if response.status_code == 200:
                data = response.json()
                interpretations = data.get("transits", [])
                if interpretations:
                    st.subheader(f"🪐 Transits astrologiques du {date_transit.strftime('%d/%m/%Y')}")
                    for t in interpretations:
                        p1 = traductions.get(t["transit_planet"], t["transit_planet"])
                        p2 = traductions.get(t["natal_planet"], t["natal_planet"])
                        aspect = traductions_aspects.get(t["aspect_type"].lower(), t["aspect_type"].lower())
                        orb = t.get("orb", "?")
                        st.markdown(f"**{p1}** en transit est en *{aspect}* avec **{p2}** natal *(orbe {orb:.1f}°)*")
                        if "transit_report" in t:
                            st.write(t["transit_report"])
                else:
                    st.info("Aucun transit significatif détecté ce jour-là.")

                    resume_transits = []
                    for t in interpretations:
                        p1 = traductions.get(t["transit_planet"], t["transit_planet"])
                        p2 = traductions.get(t["natal_planet"], t["natal_planet"])
                        aspect = traductions_aspects.get(t["aspect_type"].lower(), t["aspect_type"].lower())
                        orb = t.get("orb", "?")
                        resume_transits.append(f"{p1} {aspect} {p2} (orbe {orb:.1f}°)")
                        st.markdown(f"**{p1}** en transit est en *{aspect}* avec **{p2}** natal *(orbe {orb:.1f}°)*")
                        if "transit_report" in t and t["transit_report"]:
                            st.write(t["transit_report"])

        # 💬 Si aucun texte explicite : on appelle l’IA
                    has_interpretation = any("transit_report" in t and t["transit_report"] for t in interpretations)
                    if not has_interpretation:
                        st.info("Aucune interprétation fournie par l’API. Je vais demander à l’IA de l’interpréter.")
                        prompt = (
                        f"Voici le thème natal de la personne : {', '.join(st.session_state['planet_lines'])}.\n"
                        f"Et voici les transits astrologiques détectés pour le {date_transit.strftime('%d/%m/%Y')} :\n"
                        + "\n".join(resume_transits) +
                        "\n\nPeux-tu faire une interprétation astrologique de ces transits, dans un style "
                        + ("poétique et inspirant" if style_ia == "🌙 Poétique et inspirante" else "classique et rigoureux") + " ?"
                        )

                    try:
                        ia_response = openai.chat.completions.create(
                            model="gpt-4-turbo",
                            messages=[
                            {"role": "system", "content": "Tu es un astrologue expérimenté."},
                            {"role": "user", "content": prompt}
                            ]
                        ).choices[0].message.content

                        st.subheader("💫 Interprétation des transits (IA)")
                        st.write(ia_response)

                    except Exception as e:
                        st.error(f"Erreur lors de la réponse de l'IA : {e}")

            else:
                st.error("Erreur lors de l’appel à l’API des transits.")
