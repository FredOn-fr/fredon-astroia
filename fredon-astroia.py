import streamlit as st

st.set_page_config(page_title="FredOn-AstroIA", layout="centered")

from services.auth_supabase import handle_google_auth, get_login_url
from services.supabase_utils import get_supabase_client
from services.email_utils import envoyer_conversation_par_mail, envoyer_message_telegram
from services.constants import _, i18n

supabase = get_supabase_client()

import jwt
import os
from dotenv import load_dotenv
load_dotenv()
from dotenv import load_dotenv
load_dotenv()
REDIRECT_URL = os.getenv("REDIRECT_URL")

with open("theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")

utilisateur_connecte = handle_google_auth()

user_data = None
if utilisateur_connecte:
    try:
        user_data_resp = supabase.table("utilisateurs").select("*").eq("user_id", utilisateur_connecte["id"]).single().execute()
        user_data = user_data_resp.data
    except:
        try:
            user_data_resp = supabase.table("utilisateurs").select("*").eq("email", utilisateur_connecte["email"]).single().execute()
            user_data = user_data_resp.data
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer les données Supabase : {e}")

login_url = get_login_url(SUPABASE_URL, REDIRECT_URL)

# === SIDEBAR
with st.sidebar:
    langue = st.selectbox("🌐 Langue / Language", ["Français", "English"])
    st.session_state["langue"] = langue

    if utilisateur_connecte:
        st.markdown(f"👤 Connecté : **{utilisateur_connecte['email']}**")

        with st.expander(f"✨ {_('my_space', st.session_state["langue"])}", expanded=True):
            st.success(f"✅ {_('daily_notification', st.session_state["langue"])}")
            st.markdown(f"🗂️ {_('data_saved', st.session_state["langue"])}")
            st.markdown(f"🪐 {_('transits_info', st.session_state["langue"])}")
            st.markdown(f"💌 {_('chat_anytime', st.session_state["langue"])}")
    else:
        st.markdown(f"### 🔐 {_('login_title', st.session_state["langue"])}")
        st.markdown(f"{_('login_text', st.session_state["langue"])}")
        st.markdown(
            f"""
            <a href="{login_url}" target="_self">
                <button>{_('login_google', st.session_state["langue"])}</button>
            </a>
            """,
            unsafe_allow_html=True
        )

    if st.button(f"🚪 {_('logout', st.session_state["langue"])}"):
        st.session_state.clear()
        st.rerun()

honeypot_placeholder = st.empty()  # conteneur vide

with honeypot_placeholder.container():
    honey = st.text_input(" ", key="honey", label_visibility="collapsed")

# Après 100 ms, on vide le bloc (il disparaît sans laisser de trace)
import time
time.sleep(0.1)
honeypot_placeholder.empty()

if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

if "lieu_verifie" not in st.session_state:
    st.session_state["lieu_verifie"] = False
if "ville_trouvee" not in st.session_state:
    st.session_state["ville_trouvee"] = None

tabs = st.tabs([
    _("tab_natal", st.session_state["langue"]),
    _("tab_synastry", st.session_state["langue"]),
    _("tab_transits", st.session_state["langue"]),
    _("tab_account", st.session_state["langue"]),
    _("tab_contact", st.session_state["langue"])
])

with tabs[0]:

    st.markdown(f"""
        <div style='text-align: center; font-size: 1.5em;'>
            🧬 <strong>{_('welcome', st.session_state['langue'])}</strong>
        </div>
    """, unsafe_allow_html=True)

    import requests
    import openai
    import os
    import time
    from dotenv import load_dotenv
    from requests.auth import HTTPBasicAuth
    import smtplib
    from email.message import EmailMessage
    from services.astro_api import get_natal_wheel_chart, get_planet_positions, get_aspects
    from services.templates import generer_fichier_html, generer_discussion_html
    from services.ia_engine import generer_interpretation_ia, generer_reponse_chat, get_system_prompt

    # === CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ===
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    USER_ID = os.getenv("ASTROLOGYAPI_USER_ID")
    API_KEY = os.getenv("ASTROLOGYAPI_API_KEY")

    st.markdown(f"""
        <div style='text-align: center; margin-top: 0.5em;'>
            <h1 style='color: #5E4AE3; font-family: Georgia, sans-serif; font-size: 2.8em; margin: 0;'>FredOn-AstroIA</h1>
            <div style="font-size: 2em; margin: 0.1em 0;">🔮</div>
            <h2 style='color: #5E4AE3; font-family: Georgia, sans-serif; font-weight: bold; margin: 0;'>
                {_('astro_title', st.session_state['langue'])}
            </h2>
            <p style='font-size: 1.1em; color: white; max-width: 600px; margin: 1em auto 0;'>
                {_('astro_intro', st.session_state['langue'])}
            </p>
            <br>
        </div>
    """, unsafe_allow_html=True)

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

    def get_longitude(degree, minute, sign):
        try:
            index = signs.index(sign)
            return index * 30 + degree + minute / 60
        except:
            return None
        
    from services.constants import signs, traductions, traductions_aspects

        # === SAISIE ===
        
    with st.form("form_verif_ville"):
        nom = st.text_input(_('first_name', st.session_state["langue"]), value=user_data.get("nom") if user_data else "")
        col1, col2, col3 = st.columns(3)
        with col1:
            day = st.number_input(_('day', st.session_state["langue"]), 1, 31, value=int(user_data["birth_date"].split("-")[2]) if user_data and user_data.get("birth_date") else 1)
        with col2:
            month = st.number_input(_('month', st.session_state["langue"]), 1, 12, value=int(user_data["birth_date"].split("-")[1]) if user_data and user_data.get("birth_date") else 1)
        with col3:
            year = st.number_input(_('year', st.session_state["langue"]), 1900, 2100, value=int(user_data["birth_date"].split("-")[0]) if user_data and user_data.get("birth_date") else 1990)
        col4, col5 = st.columns(2)
        with col4:
            hour = st.number_input(_('hour', st.session_state["langue"]), 0, 23, value=int(user_data["birth_time"].split(":")[0]) if user_data and user_data.get("birth_time") else 12)
        with col5:
            minute = st.number_input(_('minute', st.session_state["langue"]), 0, 59, value=int(user_data["birth_time"].split(":")[1]) if user_data and user_data.get("birth_time") else 0)

        st.markdown(
            f"<p style='color: orange; font-size: 0.9em;'>{_('birth_time_note', st.session_state["langue"])}</p>",
            unsafe_allow_html=True
        )

        if hour == 0 and minute == 0:
            message_fr = "⚠️ Tu as indiqué 0h00. Si tu ne connais pas ton heure exacte de naissance, sache que cela peut grandement influencer la précision de ton thème astrologique."
            message_en = "⚠️ You entered 12:00 AM. If you don't know your exact time of birth, this may significantly affect the accuracy of your chart."
            st.warning(message_fr if st.session_state["langue"] == "Français" else message_en)
        ville = st.text_input(
            _('birth_city', st.session_state['langue']),
            value=user_data.get("ville") if user_data and user_data.get("ville") else ""
        )

        style_options = [ _('inspirante', st.session_state["langue"]), _('analytique', st.session_state["langue"]) ]
        style_ia = st.radio(
            _('style_ia', st.session_state["langue"]),
            style_options,
            index=0 if (not user_data or user_data.get("style") == "✨ Inspirant") else 1
        )

        verifier = st.form_submit_button(_('verify_city', st.session_state['langue']))

    if verifier and ville.strip():
        lat, lon, location_name = get_coords_from_google(ville)
        if lat and lon:
            st.success(_('location_found', st.session_state["langue"]).format(location=location_name))
            st.write(f"🌐 Latitude : {lat}, Longitude : {lon}")
            confirmer_ville = st.radio(
                _( "city_confirm", st.session_state["langue"]),
                [ _("yes_city", st.session_state["langue"]), _("no_city", st.session_state["langue"]) ],
                index=0,
                key="confirmer_ville_radio"
            )
            if confirmer_ville == _("yes_city", st.session_state["langue"]):
                st.session_state["lieu_verifie"] = True
                st.session_state["ville_trouvee"] = {
                    "lat": lat, "lon": lon, "name": location_name,
                    "nom": nom, "day": day, "month": month, "year": year,
                    "hour": hour, "minute": minute, "style_ia": style_ia
                }
        else:
            st.error(_("city_error", st.session_state["langue"]))
            st.session_state["lieu_verifie"] = False

    if st.session_state.get("lieu_verifie") and st.session_state.get("ville_trouvee"):
        st.markdown("---")
        st.subheader(_("check_theme", st.session_state["langue"]))
        if st.button(_("generate_chart", st.session_state["langue"])):
            data = st.session_state["ville_trouvee"]
            lat, lon, location_name = data["lat"], data["lon"], data["name"]
            nom = data["nom"]
            day, month, year = data["day"], data["month"], data["year"]
            hour, minute = data["hour"], data["minute"]
            style_ia = data["style_ia"]

            if honey.strip() != "":
                st.error(_("robot_error", st.session_state["langue"]))
            elif time.time() - st.session_state["start_time"] < 2:
                st.warning(_("too_fast", st.session_state["langue"]))
            else:
                tzone = get_timezone(lat, lon, year, month, day)
                st.write(f"🌐 Lat : {lat}, Lon : {lon} | UTC{tzone:+.1f}")

                birth_data = {
                    "day": int(day), "month": int(month), "year": int(year),
                    "hour": int(hour), "min": int(minute),
                    "lat": lat, "lon": lon, "tzone": tzone
                }
                with st.spinner(_( "generating_chart", st.session_state["langue"] )):
                    chart_response = get_natal_wheel_chart(birth_data)
                    if chart_response and "chart_url" in chart_response:
                        st.session_state["chart_url"] = chart_response["chart_url"]

                    planets_data = get_planet_positions({**birth_data, "hsys": "placidus"})
                    planet_lines = []
                    if isinstance(planets_data, list):
                        for p in planets_data:
                            if st.session_state["langue"] == "Français":
                                name = traductions.get(p["name"], p["name"])
                                sign = traductions.get(p["sign"], p["sign"])
                            else:
                                name = p["name"]
                                sign = p["sign"]
                            house = p.get("house", "?")
                            if st.session_state["langue"] == "Français":
                                line = f"{name} en {sign} et maison {house}"
                            else:
                                line = f"{name} in {sign} and house {house}"
                            planet_lines.append(line)

                        st.session_state["planet_lines"] = planet_lines

                    horoscope_data = get_aspects(birth_data)
                    aspects_lines = []
                    if horoscope_data and "aspects" in horoscope_data:
                        aspects = horoscope_data.get("aspects", [])
                        for asp in aspects:
                            planets = asp.get("planets", ["?", "?"])
                            if len(planets) == 2:
                                planet1 = traductions.get(asp.get("aspecting_planet", "?"), asp.get("aspecting_planet", "?"))
                                planet2 = traductions.get(asp.get("aspected_planet", "?"), asp.get("aspected_planet", "?"))
                                aspect_type_en = str(asp.get("type", "aspect inconnu")).lower()
                                if st.session_state["langue"] == "Français":
                                    aspect_type = traductions_aspects.get(aspect_type_en, aspect_type_en)
                                else:
                                    aspect_type = aspect_type_en
                                orb = asp.get("orb", "?")
                                aspects_lines.append(f"{planet1} {aspect_type} {planet2} (orbe {orb:.1f}°)")
                            else:
                                st.warning(f"Aspects mal formé : {asp}")
                        st.session_state["aspects_lines"] = aspects_lines

                        resume_theme = f"Voici le thème natal de {nom}, né le {day}/{month}/{year} à {hour:02d}:{minute:02d} à {location_name}."
                        resume_theme += " Planètes : " + ", ".join(planet_lines) + "."
                        resume_theme += " Aspects : " + ", ".join(aspects_lines) + "."

                        if st.session_state["langue"] == "English":
                            if style_ia.startswith("🌙"):
                                user_prompt = resume_theme + " Give an inspiring, supportive and encouraging astrological interpretation of this chart."
                            else:
                                user_prompt = resume_theme + " Provide a structured, precise and analytical astrological interpretation of this chart."
                        else:
                            if style_ia.startswith("🌙"):
                                user_prompt = resume_theme + " Fais une interprétation astrologique inspirante, bienveillante et encourageante de ce thème."
                            else:
                                user_prompt = resume_theme + " Donne une interprétation astrologique analytique, structurée et précise de ce thème."

                        interpretation = generer_interpretation_ia(user_prompt, style_ia, st.session_state["langue"])

                        st.session_state["resume_theme"] = resume_theme
                        st.session_state["interpretation"] = interpretation
                        st.session_state["theme_genere"] = True

                        if "email" in st.session_state:
                            supabase_data = {
                                "email": st.session_state["email"],
                                "user_id": utilisateur_connecte["id"],  # ✅ nouvel ID
                                "nom": nom,
                                "birth_date": f"{year}-{month:02d}-{day:02d}",
                                "birth_time": f"{hour:02d}:{minute:02d}",
                                "ville": location_name,
                                "aspects": ", ".join(st.session_state["aspects_lines"]),
                                "positions_planetes": ", ".join(st.session_state["planet_lines"]),
                                "style": style_ia,
                            }
                            try:
                                supabase.table("utilisateurs").upsert(supabase_data, on_conflict=["email"]).execute()
                                st.success("🎉 Ton thème est enregistré et tu recevras bientôt des notifications personnalisées.")
                            except Exception as e:
                                st.error(f"⚠️ Erreur d’enregistrement dans Supabase : {e}")

                        st.success("✨ Thème généré avec succès ! Découvre ton interprétation ci-dessous.")
                
    # ✅ Affichage persistant si thème généré

    import io

    # ✅ Vérification avant d'utiliser les clés de session_state
    if all(st.session_state.get(k) for k in ("resume_theme", "planet_lines", "aspects_lines", "interpretation", "chart_url")):
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
        st.subheader(_("chart_image", st.session_state["langue"]))
        st.image(st.session_state["chart_url"])

    if "planet_lines" in st.session_state and st.session_state["planet_lines"]:
        st.subheader(_("planet_positions", st.session_state["langue"]))
        for line in st.session_state.get("planet_lines", []):
            st.write(f"🪐 {line}")

    if "aspects_lines" in st.session_state and st.session_state["aspects_lines"]:
        st.subheader(_("aspects", st.session_state["langue"]))
        for line in st.session_state["aspects_lines"]:
            st.write(f"🔹 {line}")

    if "interpretation" in st.session_state and st.session_state["interpretation"]:
        if style_ia == "✨ Inspirant":
            if style_ia == "✨ Inspirant":
                st.subheader(_("inspirante_label", st.session_state["langue"]))
            else:
                st.subheader(_("analytique_label", st.session_state["langue"]))

        st.write(st.session_state["interpretation"])

        # ✅ Proposition de connexion Google après interprétation
        st.markdown("---")
        st.markdown(_( "daily_gift", st.session_state["langue"]))

        st.markdown(
            f"""
            <a href="{login_url}">
                <button style="padding:14px 24px;font-size:16px;border-radius:10px;background-color:#5E4AE3;color:white;">
                    {_('daily_google_btn', st.session_state["langue"])}
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    import logging
    logging.basicConfig(level=logging.ERROR, filename="app.log")

        # === CHATBOT AVEC GPT-3.5 ===
    if st.session_state.get("theme_genere"):

        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = [
                {"role": "system", "content": "Tu es un astrologue bienveillant et poétique."},
                {"role": "user", "content": "Bonjour"},
                {"role": "assistant", "content": "Bonjour 🌟 Que souhaites-tu explorer dans ton thème natal ?"}
            ]

        st.markdown("---")
        st.subheader(_("chat_with_ai", st.session_state["langue"]))

        for msg in st.session_state["chat_messages"][2:]:
            role = "Toi" if msg["role"] == "user" else "Astro-IA"
            st.markdown(f"**{role} :** {msg['content']}")

        # Avant le champ text_input
        if "clear_input" in st.session_state and st.session_state["clear_input"]:
            st.session_state["new_chat_input"] = ""
            st.session_state["clear_input"] = False

        st.markdown("#### 💡 Exemples de questions à poser :")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(_("ex1_question", langue), key="ex1"):
                st.session_state["new_chat_input"] = _("ex1_text", langue)
        with col2:
            if st.button(_("ex2_question", langue), key="ex2"):
                st.session_state["new_chat_input"] = _("ex2_text", langue)

        col3, col4 = st.columns(2)
        with col3:
            if st.button(_("ex3_question", langue), key="ex3"):
                st.session_state["new_chat_input"] = _("ex3_text", langue)
        with col4:
            if st.button(_("ex4_question", langue), key="ex4"):
                st.session_state["new_chat_input"] = _("ex4_text", langue)

        col5, col6 = st.columns(2)
        with col5:
            if st.button(_("ex5_question", langue), key="ex5"):
                st.session_state["new_chat_input"] = _("ex5_text", langue)
        with col6:
            if st.button(_("ex6_question", langue), key="ex6"):
                st.session_state["new_chat_input"] = _("ex6_text", langue)

        # Le champ
        user_input = st.text_input(_("ask_question", st.session_state["langue"]), key="new_chat_input")
        send_button = st.button(_("send_question", st.session_state["langue"]))

        # Limite d'utilisation pour les non-connectés
        if "email" not in st.session_state:
            if "question_count" not in st.session_state:
                st.session_state["question_count"] = 0
            if st.session_state["question_count"] >= 5:
                st.warning("🚫 Tu as atteint la limite de 5 questions. Connecte-toi pour continuer à discuter avec Astro-IA.")
                send_button = False

        st.markdown(f"🎛️ Style actuel d’interprétation : **{style_ia}**")

        if send_button and user_input.strip():
            system_prompt = get_system_prompt(style_ia, st.session_state["langue"])

            messages = [{"role": "system", "content": system_prompt}]

            # Injecte le contexte du thème si disponible
            if all(k in st.session_state for k in ("resume_theme", "planet_lines", "aspects_lines")):
                contexte = (
                    st.session_state["resume_theme"] + "\n\n" +
                    "Planètes : " + ", ".join(st.session_state["planet_lines"]) + "\n" +
                    "Aspects : " + ", ".join(st.session_state["aspects_lines"])
                )
                messages.append({"role": "user", "content": f"Voici mon thème natal :\n{contexte}"})
                messages.append({"role": "assistant", "content": "Merci pour ton thème natal, je m'en servirai pour mes réponses."})

            messages.append({"role": "user", "content": user_input})

            reponse_ia = generer_reponse_chat(messages)

            if "email" not in st.session_state:
                st.session_state["question_count"] += 1

            import datetime

            # Création ou ajout au fichier log
            with open("conversation_log.txt", "a", encoding="utf-8") as log_file:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"\n---\n[{timestamp}]\n")
                
                if "email" in st.session_state:
                    log_file.write(f"Utilisateur : {st.session_state['email']}\n")
                elif "nom" in st.session_state:
                    log_file.write(f"Utilisateur : {st.session_state['nom']}\n")

                log_file.write(f"Question : {user_input}\n")
                log_file.write(f"Réponse : {reponse_ia}\n")

            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            st.session_state["chat_messages"].append({"role": "assistant", "content": reponse_ia})
            st.session_state["clear_input"] = True
            st.rerun()

        # 🔽 Export discussion
        if st.session_state["chat_messages"]:
            html_discussion = generer_discussion_html(nom, st.session_state["chat_messages"])

            st.download_button(
                label=_("download_chart", st.session_state["langue"]),
                data=html_discussion,
                file_name=f"discussion_{nom}.html",
                mime="text/html"
            )

with tabs[1]:  # Synastrie
    st.subheader(_("synastry_title", st.session_state["langue"]))
    st.info("🔧 La fonctionnalité de synastrie (comparaison entre deux thèmes) est en cours de développement. Reviens bientôt !")

    if "email" in st.session_state:
        st.markdown("---")
        st.subheader(_("explore_transits", st.session_state["langue"]))
    else:
        st.warning("Connecte-toi pour accéder à cette fonctionnalité.")

with tabs[2]:  # Transits
    st.header(_("transits_title", st.session_state["langue"]))
    st.info("🔧 Cette section te permettra bientôt d'explorer les transits jour par jour. Patience cosmique… 🌌")

    import datetime
    import logging
    logging.basicConfig(level=logging.ERROR, filename="app.log")

    if "email" in st.session_state:
        st.markdown("---")
        st.subheader(_("explore_transits", st.session_state["langue"]))
    else:
       st.warning("Connecte-toi pour accéder à cette fonctionnalité.")

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

            try:
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

                    # ➕ Synthèse des transits
                    resume_transits = []
                    for t in interpretations:
                        p1 = traductions.get(t["transit_planet"], t["transit_planet"])
                        p2 = traductions.get(t["natal_planet"], t["natal_planet"])
                        aspect = traductions_aspects.get(t["aspect_type"].lower(), t["aspect_type"].lower())
                        orb = t.get("orb", "?")
                        resume_transits.append(f"{p1} {aspect} {p2} (orbe {orb:.1f}°)")
                        if "transit_report" in t and t["transit_report"]:
                            st.write(t["transit_report"])

                    # 🔍 S'il n'y a aucune interprétation API : on demande à l'IA
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
                            logging.error(f"[Erreur GPT-4 - Transits] {e}")
                            st.error("❌ Une erreur est survenue pendant l’analyse des transits. Réessaie plus tard.")
                else:
                    st.error("❌ Erreur lors de l’appel à l’API des transits.")

            except Exception as e:
                logging.error(f"[Erreur API Transits] {e}")
                st.error("❌ Une erreur technique est survenue. Réessaie plus tard.")

with tabs[3]:  # Onglet "Mon compte"

    import streamlit as st

    st.title(_("account_title", st.session_state["langue"]))

    # Vérifie si l'utilisateur est connecté
    if "email" in st.session_state:
        email = st.session_state["email"]
        st.success(f"Tu es connecté avec l'adresse : {email}")

        st.markdown("---")
        st.subheader(_("saved_data_title", st.session_state["langue"]))

        # 📋 Récapitulatif des données astrologiques
        with st.expander(_("astro_summary", st.session_state["langue"]), expanded=True):
            infos = []

            if "nom" in st.session_state:
                infos.append(("🧑 Nom", st.session_state["nom"]))

            if "birth_date" in user_data:
                infos.append(("📅 Date de naissance", user_data["birth_date"]))

            if "birth_time" in user_data:
                infos.append(("⏰ Heure de naissance", user_data["birth_time"]))

            if "ville" in user_data:
                infos.append(("📍 Ville de naissance", user_data["ville"]))

            if "style" in user_data:
                infos.append(("✨ Style IA", user_data["style"]))

            if "notifications_ok" in user_data:
                notif_status = "✅ Activées" if user_data["notifications_ok"] else "❌ Désactivées"
                infos.append(("📨 Notifications par mail", notif_status))

            for label, value in infos:
                st.markdown(f"**{label}** : {value}")

        # Affichage conditionnel des données (si elles existent)
        planet_lines = st.session_state.get("planet_lines")
        if isinstance(planet_lines, list) and planet_lines:
            st.markdown("### 🌟 Positions des planètes")
            for line in planet_lines:
                st.write(f"🪐 {line}")

        aspects_lines = st.session_state.get("aspects_lines")
        if isinstance(aspects_lines, list) and aspects_lines:
            st.markdown("### 🪐 Aspects astrologiques")
            for line in aspects_lines:
                st.write(f"🔹 {line}")

        if "style" in st.session_state:
            st.markdown("### ✨ Style d'interprétation préféré")
            st.write(f"{st.session_state['style']}")

        st.markdown("---")
        st.markdown("---")
        st.subheader("🔔 Notifications")

        notifications_ok = user_data.get("notifications_ok", True)

        notifications_checkbox = st.checkbox(
            _("daily_email_optin", st.session_state["langue"]),
            value=notifications_ok
        )

        if notifications_ok:
            st.info(_("notifications_enabled", st.session_state["langue"]))
        else:
            st.warning(_("notifications_disabled", st.session_state["langue"]))

        if notifications_checkbox != notifications_ok:
            try:
                supabase.table("utilisateurs").update({
                    "notifications_ok": notifications_checkbox
                }).eq("user_id", utilisateur_connecte["id"]).execute()
                st.success("✅ Préférence mise à jour.")
                user_data["notifications_ok"] = notifications_checkbox
            except Exception as e:
                st.error("❌ Erreur lors de la mise à jour des préférences.")

    else:
        st.warning("Tu n'es pas encore connecté. Merci de te connecter pour accéder à ton espace personnel.")

with tabs[4]:  # Onglet "Me contacter"
    
    st.header(_("tab_contact", st.session_state["langue"]))

    from dotenv import load_dotenv
    load_dotenv()

    st.markdown("Tu veux me poser une question ou me faire un retour ? Utilise l’un des moyens ci-dessous :")

    if "email" in st.session_state:
        st.markdown(f"✉️ Tu es connecté avec : `{st.session_state['email']}`")
    else:
        st.info("Tu peux quand même envoyer un message, mais tu n'es pas connecté.")

    with st.expander("✉️ Envoyer un email directement depuis l’app"):
        with st.form("form_email_contact"):
            nom_contact = st.text_input("Ton prénom ou pseudo")
            email_contact = st.text_input("Ton adresse email")
            message_contact = st.text_area("Ton message")
            envoyer = st.form_submit_button("📨 Envoyer")

        if envoyer:
            if not email_contact or not message_contact:
                st.warning("Merci de renseigner ton adresse email et ton message.")
            else:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = f"[FredOn-AstroIA] Message de {nom_contact}"
                    msg['From'] = os.getenv("SMTP_USER")
                    msg['To'] = os.getenv("SMTP_USER")
                    msg.set_content(f"Message de {nom_contact} <{email_contact}> :\n\n{message_contact}")

                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
                        smtp.send_message(msg)

                    st.success("✅ Message envoyé avec succès ! Je te répondrai dès que possible.")
                except Exception as e:
                    logging.error(f"[Erreur envoi email contact] {e}")
                    st.error("❌ Une erreur est survenue lors de l’envoi de l’email. Réessaie plus tard.")

    with st.expander("💬 Laisser un message (envoi direct au créateur via Telegram)"):
        pseudo = st.text_input("Ton prénom ou pseudo", key="telegram_pseudo")
        message = st.text_area("Ton message ici", key="telegram_message")

        if st.button("📨 Envoyer via Telegram"):
            if message.strip():
                contenu = f"💬 Nouveau message de {pseudo or 'anonyme'} :\n\n{message}"
                try:
                    envoyer_message_telegram(contenu)
                    st.success("✅ Ton message a été envoyé instantanément !")
                except Exception as e:
                    logging.error(f"[Erreur Telegram] {e}")
                    st.error("❌ Problème d'envoi via Telegram.")
            else:
                st.warning("Le message est vide… 😅")


