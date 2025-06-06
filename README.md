
# FredOn-AstroIA 🌌✨

**FredOn-AstroIA** est une application interactive développée avec **Streamlit** qui permet d'explorer son thème natal astrologique, discuter avec une IA astrologue bienveillante, et recevoir des interprétations personnalisées. Elle combine des APIs astrologiques, OpenAI, Supabase et une interface fluide.

---

## 🔧 Fonctionnalités

- 🔐 Connexion via **Google OAuth** (Supabase)
- 🌠 Génération complète de **thème natal**
- 🤖 Dialogue IA (GPT-4 pour l'interprétation, GPT-3.5 pour le chat)
- 📩 Export HTML de l’analyse + envoi par mail ou Telegram
- 🌍 Géolocalisation automatique par nom de ville (Google / LocationIQ)
- 🪐 Analyse des transits astrologiques
- 💾 Sauvegarde des données utilisateur (Supabase)
- 🎨 UI soignée et responsive via Streamlit

---

## 🗂 Structure du projet

```
FredOn-AstroIA/
│
├── app.py                         # Point d’entrée principal Streamlit
├── redirect.html                  # Redirection OAuth (convertit #access_token)
│
├── .env                           # Variables d’environnement
│
├── services/
│   ├── auth_supabase.py           # Authentification Google (Supabase)
│   ├── supabase_utils.py          # Client Supabase
│   ├── astro_api.py               # Appels à AstrologyAPI
│   ├── ia_engine.py               # Appels à GPT-4 et GPT-3.5
│   ├── email_utils.py             # Envoi mail / Telegram
│   ├── templates.py               # Génération HTML
│   └── constants.py               # Signes, traductions, aspects
```

---

## 🚀 Lancer le projet en local

### 1. Prérequis
- Python ≥ 3.9
- Compte Supabase
- Clés API :
  - OpenAI
  - AstrologyAPI
  - Google Maps ou LocationIQ
  - SMTP + Telegram (optionnel)

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Remplir le fichier `.env`

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
ASTROLOGYAPI_USERID=...
ASTROLOGYAPI_KEY=...
ASTROLOGYAPI_AUTH=...

GOOGLE_MAPS_API_KEY=...
LOCATIONIQ_KEY=...

OPENAI_API_KEY=...

SMTP_USER=...
SMTP_PASS=...

TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### 4. Servir `redirect.html` sur un autre port

```bash
python -m http.server 8502
```

Ajoute dans Supabase :
```
http://localhost:8502/redirect.html
```

### 5. Lancer l’app

```bash
streamlit run app.py
```

---

## 🧠 À propos

Développé avec ❤️ par Fredon pour une exploration poétique et éducative de l’astrologie moderne.

---

## 🪄 Démo à venir ?

- ✅ Support multilingue
- 🔮 Personnalisation des notifications
- 📆 Calendrier des transits

---

## 📬 Contact

Tu peux utiliser l’onglet “Me contacter” directement dans l’app ou envoyer un message via Telegram intégré !

---
