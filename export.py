import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime


def generer_synthese(prenom, total, annee_pic, valeur_pic, derniere_annee, rang_affiche):
    total_affiche = f"{total:,}".replace(",", " ")
    return (
        f"<strong>{prenom}</strong> a été donné {total_affiche} fois sur la période sélectionnée. "
        f"Son pic de popularité a été atteint en {annee_pic}, avec {valeur_pic} naissances cette année-là. "
        f"En {derniere_annee}, son classement était : {rang_affiche} (rang national)."
    )


def generer_rapport_html(prenoms, df_pivot, recaps, periode_min, periode_max, zone_selectionnee, figures_cartes=None):
    # ---- Graphique d'évolution ----
    fig_export = go.Figure()
    for colonne in df_pivot.columns:
        fig_export.add_trace(go.Scatter(
            x=df_pivot.index, y=df_pivot[colonne], mode="lines", name=colonne
        ))
    fig_export.update_layout(
        title=None,
        xaxis_title="Année", yaxis_title="Naissances",
        template="plotly_white",
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=20, b=40, l=50, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    graphique_html = pio.to_html(
        fig_export, include_plotlyjs="cdn", full_html=False,
        config={"displayModeBar": False, "responsive": True},
        default_width="100%", default_height="420px"
    )

    # ---- Cartes ----
    cartes_html = ""
    if figures_cartes:
        cartes_items = ""
        nb_cartes = len(figures_cartes)
        for i, fig_carte in enumerate(figures_cartes):
            fig_carte_export = go.Figure(fig_carte)
            fig_carte_export.update_layout(
                paper_bgcolor="white", plot_bgcolor="white", geo=dict(bgcolor="white"),
                margin=dict(t=40, b=10, l=10, r=10),
                autosize=True,
                coloraxis_colorbar=dict(len=0.75, thickness=14)
            )
            carte_rendue = pio.to_html(
                fig_carte_export, include_plotlyjs=False, full_html=False,
                config={"displayModeBar": False, "responsive": True},
                default_width="100%", default_height="420px"
            )
            # Si nombre impair de cartes, la dernière occupe toute la largeur
            classe_extra = " full-width" if (nb_cartes % 2 == 1 and i == nb_cartes - 1) else ""
            cartes_items += f'<div class="carte-item{classe_extra}">{carte_rendue}</div>'

        cartes_html = f"""
        <div class="section">
            <h2>Répartition géographique</h2>
            <div class="cartes-grid">{cartes_items}</div>
        </div>
        """

    # ---- Fiches récapitulatives ----
    recaps_items = ""
    liste_recaps = list(recaps.items())
    nb_recaps = len(liste_recaps)
    for i, (prenom, (total, annee_pic, valeur_pic, derniere_annee, rang_affiche)) in enumerate(liste_recaps):
        total_affiche = f"{total:,}".replace(",", " ")
        synthese = generer_synthese(prenom, total, annee_pic, valeur_pic, derniere_annee, rang_affiche)
        classe_extra = " full-width" if (nb_recaps % 2 == 1 and i == nb_recaps - 1) else ""
        recaps_items += f"""
        <div class="recap-card{classe_extra}">
            <h3>{prenom}</h3>
            <div class="recap-stats">
                <div class="stat">
                    <div class="stat-label">Naissances (période)</div>
                    <div class="stat-value">{total_affiche}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Pic de popularité</div>
                    <div class="stat-value">{annee_pic}</div>
                    <div class="stat-sub">{valeur_pic} naissances</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Rang en {derniere_annee} (national)</div>
                    <div class="stat-value">{rang_affiche}</div>
                </div>
            </div>
            <p class="synthese">{synthese}</p>
        </div>
        """

    date_generation = datetime.now().strftime("%d/%m/%Y")
    zone_texte = zone_selectionnee if zone_selectionnee else "France entière"

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
                font-size: 15px;
                line-height: 1.5;
                background-color: #FBF7F0;
                color: #3B2F2A;
                margin: 0;
                padding: 0;
            }}
            h1, h2, h3 {{
                font-family: Georgia, 'Times New Roman', serif;
            }}
            .page {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }}
            header {{
                border-bottom: 3px solid #8B5E3C;
                padding-bottom: 1.25rem;
                margin-bottom: 2rem;
            }}
            header h1 {{
                color: #8B5E3C;
                margin: 0 0 0.5rem 0;
                font-size: 1.9rem;
            }}
            .meta-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.85rem;
                margin-top: 0.75rem;
            }}
            .meta-table td {{
                padding: 0.2rem 0;
                opacity: 0.8;
            }}
            .meta-table td:first-child {{
                font-weight: 600;
                width: 140px;
                opacity: 1;
            }}
            .section {{
                margin-bottom: 2.5rem;
            }}
            .section h2 {{
                font-size: 1.2rem;
                color: #8B5E3C;
                border-bottom: 1px solid #D8C9B4;
                padding-bottom: 0.4rem;
                margin-bottom: 1.25rem;
            }}
            .recap-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }}
            .recap-card {{
                background-color: #EFE6D8;
                border-radius: 0.6rem;
                padding: 1.25rem 1.5rem;
                min-width: 0;
            }}
            .recap-card.full-width {{
                grid-column: 1 / -1;
            }}
            @media (max-width: 860px) {{
                .recap-grid {{
                    grid-template-columns: 1fr;
                }}
                .recap-card.full-width {{
                    grid-column: 1;
                }}
            }}
            .recap-card h3 {{
                margin: 0 0 0.9rem 0;
                font-size: 1.15rem;
            }}
            .recap-stats {{
                display: flex;
                flex-wrap: wrap;
                gap: 2rem;
                margin-bottom: 0.9rem;
            }}
            .stat-label {{
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.03em;
                opacity: 0.7;
                margin-bottom: 0.15rem;
            }}
            .stat-value {{
                font-size: 1.3rem;
                font-weight: 700;
            }}
            .stat-sub {{
                font-size: 0.8rem;
                opacity: 0.7;
            }}
            .synthese {{
                font-style: italic;
                font-size: 0.92rem;
                margin: 0;
                padding-top: 0.75rem;
                border-top: 1px solid #D8C9B4;
            }}
            .cartes-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }}
            .carte-item {{
                background-color: #FFFFFF;
                border: 1px solid #E5D9C6;
                border-radius: 0.6rem;
                padding: 0.5rem;
                overflow: hidden;
                min-width: 0;
            }}
            .carte-item.full-width {{
                grid-column: 1 / -1;
            }}
            @media (max-width: 860px) {{
                .cartes-grid {{
                    grid-template-columns: 1fr;
                }}
                .carte-item.full-width {{
                    grid-column: 1;
                }}
            }}
            footer {{
                margin-top: 3rem;
                padding-top: 1rem;
                border-top: 1px solid #D8C9B4;
                font-size: 0.75rem;
                opacity: 0.6;
                text-align: center;
            }}
            @media print {{
                body {{ background-color: white; }}
                .section {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="page">
            <header>
                <h1>Explorateur des prénoms français</h1>
                <table class="meta-table">
                    <tr><td>Prénom(s)</td><td>{", ".join(prenoms)}</td></tr>
                    <tr><td>Période</td><td>{periode_min} — {periode_max}</td></tr>
                    <tr><td>Zone</td><td>{zone_texte}</td></tr>
                    <tr><td>Généré le</td><td>{date_generation}</td></tr>
                </table>
            </header>

            <div class="section">
                <h2>Synthèse par prénom</h2>
                <div class="recap-grid">{recaps_items}</div>
            </div>

            <div class="section">
                <h2>Évolution du nombre de naissances</h2>
                {graphique_html}
            </div>

            {cartes_html}

            <footer>
                Données : INSEE — Rapport généré depuis le dashboard Explorateur des prénoms français
            </footer>
        </div>
    </body>
    </html>
    """
