import streamlit as st
import pandas as pd
import json
import numpy as np
import plotly.express as px
from export import generer_rapport_html

st.set_page_config(layout="wide")  # utilise toute la largeur d'écran, plus confortable avec une sidebar

st.title("Explorateur des prénoms français")
st.write("Explorez l'évolution des prénoms donnés en France depuis 1900")

# ============ CHARGEMENT DES DONNÉES ============
@st.cache_data
def load_data():
    df_national = pd.read_parquet("data/prenoms_national.parquet")
    df_geo = pd.read_parquet("data/prenoms_geo.parquet")
    return df_national, df_geo

@st.cache_data
def load_geojson():
    with open("sources/departements.geojson", encoding="utf-8") as f:
        return json.load(f)

df_national, df_geo = load_data()
geojson_dep = load_geojson()
liste_prenoms = sorted(df_national["prenom"].unique())
liste_zones = sorted(df_geo["nom_geo"].dropna().unique())

def echelle_avec_zero_blanc(nom_palette, seuil=0.03):
    couleur_debut, couleur_fin = px.colors.sample_colorscale(nom_palette, [0, 1])
    return [
        (0.0, "white"),
        (seuil, couleur_debut),
        (1.0, couleur_fin)
    ]

@st.cache_data(show_spinner=False)
def preparer_donnees_graphique(prenoms, sexes_filtres, zone, periode_min, periode_max):
    if zone:
        df_filtre = df_geo[
            (df_geo["prenom"].isin(prenoms)) & (df_geo["nom_geo"] == zone)
        ]
    else:
        df_filtre = df_national[df_national["prenom"].isin(prenoms)]

    df_filtre = df_filtre[df_filtre["sexe"].isin(sexes_filtres)]

    df_filtre = df_filtre[
        (df_filtre["periode"] >= periode_min) & (df_filtre["periode"] <= periode_max)
    ].copy()

    df_filtre["sexe_label"] = df_filtre["sexe"].map({"M": "Garçons", "F": "Filles"})
    df_filtre["serie"] = df_filtre["prenom"] + " (" + df_filtre["sexe_label"] + ")"
    return df_filtre.pivot_table(index="periode", columns="serie", values="valeur", fill_value=0)


@st.cache_data(show_spinner=False)
def preparer_donnees_carte(prenom, sexes_filtres, annee):
    df_carte = df_geo[
        (df_geo["prenom"] == prenom) & (df_geo["niveau_geographique"] == "DEP") &
        (df_geo["periode"] == annee) & (df_geo["sexe"].isin(sexes_filtres))
    ]
    df_carte = df_carte.groupby("geographie", as_index=False)["valeur"].sum()
    tous_departements = df_geo[df_geo["niveau_geographique"] == "DEP"][["geographie"]].drop_duplicates()
    df_carte = tous_departements.merge(df_carte, on="geographie", how="left")
    df_carte["valeur"] = df_carte["valeur"].fillna(0)
    df_carte["valeur_log"] = np.log1p(df_carte["valeur"])
    return df_carte


@st.cache_data(show_spinner=False)
def calculer_recap(prenom, sexes_filtres, periode_min, periode_max):
    df_p = df_national[
        (df_national["prenom"] == prenom) &
        (df_national["sexe"].isin(sexes_filtres)) &
        (df_national["periode"] >= periode_min) &
        (df_national["periode"] <= periode_max)
    ]

    if df_p.empty:
        return None

    df_par_annee = df_p.groupby("periode", as_index=False)["valeur"].sum()

    total = df_par_annee["valeur"].sum()
    idx_pic = df_par_annee["valeur"].idxmax()
    annee_pic = int(df_par_annee.loc[idx_pic, "periode"])
    valeur_pic = int(df_par_annee.loc[idx_pic, "valeur"])

    derniere_annee = df_p["periode"].max()
    df_derniere = df_p[df_p["periode"] == derniere_annee]

    return total, annee_pic, valeur_pic, derniere_annee, df_derniere


# ============ SIDEBAR : TOUS LES FILTRES ============
st.sidebar.header("Filtres")

# Sélection du sexe (filtre global, conservé pour garder le multiselect performant)
sexe_choisi = st.sidebar.multiselect(
    "Fille ou garçon ?",
    options=["Fille", "Garçon"]
)

mapping_sexe = {"Garçon": "M", "Fille": "F"}
sexes_filtres = tuple(mapping_sexe[s] for s in sexe_choisi)

# Sélection du/des prénom(s), dépend du sexe choisi
if sexes_filtres:
    liste_prenoms_filtree = sorted(
        df_national[df_national["sexe"].isin(sexes_filtres)]
        .groupby("prenom")["valeur"].sum()
        .nlargest(9000)
        .index.tolist()
    )

    # On récupère la sélection actuelle du widget, pour ne jamais la perdre
    # si l'utilisateur modifie le filtre sexe après coup
    selection_actuelle = st.session_state.get("multiselect_prenoms_light", [])
    options_affichees = sorted(set(liste_prenoms_filtree) | set(selection_actuelle))

    prenoms_selectionnes = st.sidebar.multiselect(
        "Prénom(s)",
        options=options_affichees,
        key="multiselect_prenoms_light",
        placeholder="Tapez un ou plusieurs prénoms..."
    )
else:
    prenoms_selectionnes = []
    st.sidebar.caption("Sélectionnez d'abord Fille et/ou Garçon")


#Trop lourd pour streamlit cloud, multiselect n'arrive pas à gérer les 49000 prénomns
#prenoms_selectionnes = st.sidebar.multiselect(
#    "Prénom(s)",
#    options=liste_prenoms,
#    placeholder="Tapez un ou plusieurs prénoms..."
#)


periode_min = int(df_national["periode"].min())
periode_max = int(df_national["periode"].max())

periode_selectionnee = st.sidebar.slider(
    "Période",
    min_value=periode_min,
    max_value=periode_max,
    value=(periode_min, periode_max),  # tuple = active le mode "plage" (deux curseurs)
    key="slider_periode"
)

zone_selectionnee = st.sidebar.selectbox(
    "Région ou département (optionnel)", options=liste_zones,
    index=None, placeholder="Toute la France"
)

st.sidebar.divider()
st.sidebar.subheader("Carte")
if prenoms_selectionnes:
    prenoms_carte = st.sidebar.multiselect(
        "Prénom(s) sur la carte (max 3)",
        options=prenoms_selectionnes,
        default=prenoms_selectionnes[:1],
        max_selections=3,
        key="multiselect_prenoms_carte_light"
    )
else:
    prenoms_carte = []

annee_carte = st.sidebar.slider(
    "Année (carte)", int(df_geo["periode"].min()), int(df_geo["periode"].max()), 2025
)
echelle_carte = st.sidebar.radio(
    "Échelle de la carte",
    options=["Logarithmique", "Valeurs absolues"],
    horizontal=True
)

st.sidebar.subheader("Classement")
annee_classement = st.sidebar.slider(
    "Année (classement)", int(df_national["periode"].min()), int(df_national["periode"].max()),
    2025, key="slider_classement"
)
top_n = st.sidebar.selectbox("Taille du classement", options=[5, 10, 20], index=0)

# ============ ZONE CENTRALE : GRAPHIQUE D'ÉVOLUTION ============
if prenoms_selectionnes:
    df_pivot = preparer_donnees_graphique(
        tuple(prenoms_selectionnes), sexes_filtres, zone_selectionnee,
        periode_selectionnee[0], periode_selectionnee[1]
    )

    recaps = {}
    for prenom in prenoms_selectionnes:
        resultat = calculer_recap(prenom, sexes_filtres, periode_selectionnee[0], periode_selectionnee[1])
        if resultat is None:
            with st.container(border=True):
                st.warning(
                    f"**{prenom}** n'a jamais été attribué à un(e) {'/'.join(sexe_choisi).lower()} "
                    f"sur la période sélectionnée."
                )
            continue

        total, annee_pic, valeur_pic, derniere_annee, df_derniere = resultat

        rangs_texte = []
        for _, ligne in df_derniere.iterrows():
            sexe_label = "G" if ligne["sexe"] == "M" else "F"
            rangs_texte.append(f"{sexe_label}: {int(ligne['rang'])}")
        rang_affiche = " / ".join(rangs_texte) if rangs_texte else "—"
        recaps[prenom] = (total, annee_pic, valeur_pic, derniere_annee, rang_affiche)

        with st.container(border=True):
            st.write(f"**{prenom}**")
            col1, col2, col3 = st.columns(3)
            col1.metric("Naissances (période)", f"{total:,}".replace(",", " "))
            col2.metric("Pic de popularité", f"{annee_pic}", f"{valeur_pic} naissances")
            col3.metric(f"Rang (national) en {derniere_annee}", rang_affiche)

    titre = "Évolution de : " + ", ".join(prenoms_selectionnes)
    if zone_selectionnee:
        titre += f" — {zone_selectionnee}"
    st.subheader(titre)
    st.line_chart(df_pivot)

else:
    st.markdown(
    """
    <div style="
        background-color: #EFE6D8;
        color: #3B2F2A;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #8B5E3C;
    ">
        Sélectionnez d'abord un sexe, puis un ou plusieurs prénoms dans la barre latérale pour commencer.
    </div>
    """,
    unsafe_allow_html=True
    )

# ============ ZONE CENTRALE : CARTE ============
st.subheader("Carte(s) de France")
if prenoms_carte:
    cartes_a_afficher = []
    for prenom_carte in prenoms_carte:
        df_carte = preparer_donnees_carte(prenom_carte, sexes_filtres, annee_carte)
        if df_carte["valeur"].sum() > 0:
            cartes_a_afficher.append((prenom_carte, df_carte))

    if not cartes_a_afficher and prenoms_carte:
        st.info(
            "Les données géographiques détaillées ne sont pas disponibles pour ce(s) prénom(s) "
            "sur cette année — les effectifs par département sont trop "
            "faibles pour être publiés par l'INSEE (seuil de confidentialité), bien que le total "
            "national ne soit pas nul."
        )

    figures_cartes = []

    if cartes_a_afficher:
        colonnes_carte = st.columns(len(cartes_a_afficher))

        for i, (prenom_carte, df_carte) in enumerate(cartes_a_afficher):
            if echelle_carte == "Logarithmique":
                colonne_couleur = "valeur_log"
                titre_legende = "Naissances (log)"
            else:
                colonne_couleur = "valeur"
                titre_legende = "Naissances"

            fig = px.choropleth(
                df_carte, geojson=geojson_dep, locations="geographie", featureidkey="properties.code",
                color=colonne_couleur,
                color_continuous_scale=echelle_avec_zero_blanc("Viridis"),
                scope="europe", title=f"{prenom_carte} — {annee_carte}",
                hover_data={"valeur": True, "valeur_log": False},
                labels={colonne_couleur: titre_legende}
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                geo=dict(bgcolor="rgba(0,0,0,0)")
            )
            colonnes_carte[i].plotly_chart(fig, use_container_width=True)
            figures_cartes.append(fig)
else:
    figures_cartes = []

# ============ EXPORT (CSV + rapport HTML) ============
if prenoms_selectionnes:
    csv_export = df_pivot.reset_index().to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv_export,
        file_name=f"prenoms_{'_'.join(prenoms_selectionnes)}.csv",
        mime="text/csv"
    )

    rapport_html = generer_rapport_html(
        prenoms_selectionnes, df_pivot, recaps,
        periode_selectionnee[0], periode_selectionnee[1], zone_selectionnee,
        figures_cartes
    )
    st.download_button(
        label="📄 Télécharger le rapport (HTML)",
        data=rapport_html.encode("utf-8"),
        file_name=f"rapport_{'_'.join(prenoms_selectionnes)}.html",
        mime="text/html"
    )

# ============ ZONE CENTRALE : CLASSEMENT ============
st.subheader("Classement des prénoms")
df_classement = df_national[df_national["periode"] == annee_classement]

if prenoms_selectionnes:
    st.write("**Rang du/des prénom(s) sélectionné(s) cette année-là :**")
    for prenom in prenoms_selectionnes:
        lignes = df_classement[df_classement["prenom"] == prenom]
        if lignes.empty:
            st.write(f"- {prenom} : non attribué en {annee_classement}")
        else:
            for _, ligne in lignes.iterrows():
                sexe_label = "garçons" if ligne["sexe"] == "M" else "filles"
                st.write(f"- {prenom} ({sexe_label}) : rang {int(ligne['rang'])} — {int(ligne['valeur'])} naissances")

top_garcons = (
    df_classement[(df_classement["sexe"] == "M") & (df_classement["rang"] <= top_n)]
    .sort_values("rang")[["rang", "prenom", "valeur"]].set_index("rang")
)
top_filles = (
    df_classement[(df_classement["sexe"] == "F") & (df_classement["rang"] <= top_n)]
    .sort_values("rang")[["rang", "prenom", "valeur"]].set_index("rang")
)

col_g, col_f = st.columns(2)
with col_g:
    st.write(f"**Top {top_n} garçons — {annee_classement}**")
    st.dataframe(top_garcons)
with col_f:
    st.write(f"**Top {top_n} filles — {annee_classement}**")
    st.dataframe(top_filles)
