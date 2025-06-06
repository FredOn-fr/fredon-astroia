def generer_fichier_html(nom, resume, planetes, aspects, interpretation, chart_url):
    contenu_html = f"""
    <html>
    <head>
        <meta charset=\"UTF-8\">
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
        <img src=\"{chart_url}\" alt=\"Carte du ciel\">
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
        <meta charset=\"UTF-8\">
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
