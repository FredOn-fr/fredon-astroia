import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_system_prompt(style, langue):
    if langue == "English":
        return (
            "You are a kind and inspiring astrologer who supports personal growth through a sensitive interpretation of the birth chart."
            if style.startswith("🌙") else
            "You are a rigorous and analytical astrologer who delivers structured and technical interpretations."
        )
    else:
        return (
            "Tu es un astrologue bienveillant, inspirant et chaleureux..."
            if style.startswith("🌙") else
            "Tu es un astrologue rigoureux, analytique et précis..."
        )

def generer_interpretation_ia(prompt, style="🌙", langue="Français"):
    """
    Appelle GPT-4 pour générer une interprétation astrologique à partir d'un prompt
    """
    try:
        system_prompt = get_system_prompt(style, langue)

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur IA : {e}"

def generer_reponse_chat(messages):
    """
    Appelle GPT-3.5 pour prolonger une conversation dans le style d'une astro-IA
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur IA : {e}"
