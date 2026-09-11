import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime


def generer_synthese(prenom, total, annee_pic, valeur_pic, derniere_annee, rang_affiche):
    return (
        "Le prénom " f"<strong>{prenom}</strong> a été donné au total {total:,}".replace(",", " ") + f" fois sur la période sélectionnée. "
        f"Son pic de popularité a été atteint en {annee_pic}, avec {valeur_pic} naissances cette année-là. "
        f"Et en {derniere_annee}, son classement de popularité au niveau national à atteint la {rang_affiche}ème place."
    )


def generer_rapport_html(prenoms, df_pivot, recaps, periode_min, periode_max, zone_selectionnee):
    fig_export = go.Figure()
    for colonne in df_pivot.columns:
        fig_export.add_trace(go.Scatter(
            x=df_pivot.index, y=df_pivot[colonne], mode="lines", name=colonne
        ))
    fig_export.update_layout(
        title="Évolution du nombre de naissances",
        xaxis_title="Année", yaxis_title="Naissances",
        template="plotly_white"
    )
    graphique_html = pio.to_html(fig_export, include_plotlyjs="cdn", full_html=False)

    recaps_html = ""
    for prenom, (total, annee_pic, valeur_pic, derniere_annee, rang_affiche) in recaps.items():
        total_affiche = f"{total:,}".replace(",", " ")
        synthese = generer_synthese(prenom, total, annee_pic, valeur_pic, derniere_annee, rang_affiche)
        recaps_html += f"""
        <div class="recap-card">
            <h3>{prenom}</h3>
            <p><strong>Naissances (période)</strong> : {total_affiche}</p>
            <p><strong>Pic de popularité</strong> : {annee_pic} ({valeur_pic} naissances)</p>
            <p><strong>Rang en {derniere_annee} (national)</strong> : {rang_affiche}</p>
            <p class="synthese">{synthese}</p>
        </div>
        """

    date_generation = datetime.now().strftime("%d/%m/%Y")
    zone_texte = f" — Zone : {zone_selectionnee}" if zone_selectionnee else " — Zone : France entière"

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: serif; background-color: #FBF7F0; color: #3B2F2A; padding: 2rem; }}
            h1 {{ color: #8B5E3C; }}
            .contexte {{ font-size: 0.9rem; opacity: 0.8; margin-bottom: 1.5rem; }}
            .recap-card {{
                background-color: #EFE6D8; border-radius: 0.5rem;
                padding: 1rem 1.5rem; margin-bottom: 1rem;
            }}
            .synthese {{ font-style: italic; margin-top: 0.75rem; }}
        </style>
    </head>
    <body>
        <h1>Explorateur des prénoms français</h1>
        <p class="contexte">
            Rapport généré le {date_generation} — Prénom(s) : {", ".join(prenoms)}<br>
            Période : {periode_min} - {periode_max}{zone_texte}
        </p>
        {recaps_html}
        {graphique_html}
    </body>
    </html>
    """