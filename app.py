import streamlit as st
import pandas as pd
import json
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")  # utilise toute la largeur d'écran, plus confortable avec une sidebar

st.title("Explorateur des prénoms français")
st.write("Explorez l'évolution des prénoms donnés en France depuis 1900")

# ============ CHARGEMENT DES DONNÉES (inchangé) ============
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

def echelle_avec_zero_blanc(nom_palette,seuil=0.03):
    couleur_debut, couleur_fin = px.colors.sample_colorscale(nom_palette, [0, 1])

    return [
        (0.0, "white"), 
        (seuil, couleur_debut), 
        (1.0, couleur_fin)]

@st.cache_data(show_spinner=False)
def preparer_donnees_graphique(prenoms, zone, periode_min, periode_max):
    if zone:
        df_filtre = df_geo[
            (df_geo["prenom"].isin(prenoms)) & (df_geo["nom_geo"] == zone)
        ]
    else:
        df_filtre = df_national[df_national["prenom"].isin(prenoms)]

    df_filtre = df_filtre[
        (df_filtre["periode"] >= periode_min) & (df_filtre["periode"] <= periode_max)
    ].copy()

    df_filtre["sexe_label"] = df_filtre["sexe"].map({"M": "Garçons", "F": "Filles"})
    df_filtre["serie"] = df_filtre["prenom"] + " (" + df_filtre["sexe_label"] + ")"
    return df_filtre.pivot_table(index="periode", columns="serie", values="valeur", fill_value=0)


@st.cache_data(show_spinner=False)
def preparer_donnees_carte(prenom, annee):
    df_carte = df_geo[
        (df_geo["prenom"] == prenom) & (df_geo["niveau_geographique"] == "DEP") &
        (df_geo["periode"] == annee)
    ]
    df_carte = df_carte.groupby("geographie", as_index=False)["valeur"].sum()
    tous_departements = df_geo[df_geo["niveau_geographique"] == "DEP"][["geographie"]].drop_duplicates()
    df_carte = tous_departements.merge(df_carte, on="geographie", how="left")
    df_carte["valeur"] = df_carte["valeur"].fillna(0)
    df_carte["valeur_log"] = np.log1p(df_carte["valeur"])
    return df_carte

# ============ SIDEBAR : TOUS LES FILTRES ============
st.sidebar.header("Filtres")


recherche_texte = st.sidebar.text_input(
    "Rechercher un prénom",
    placeholder="Tapez au moins 2 lettres..."
)

if len(recherche_texte) >= 2:
    options_filtrees = [p for p in liste_prenoms if p.startswith(recherche_texte.upper())][:100]
else:
    options_filtrees = []

prenoms_selectionnes = st.sidebar.multiselect(
    "Prénom(s) sélectionné(s)",
    options=options_filtrees,
    placeholder="Tapez d'abord dans le champ ci-dessus" if not recherche_texte else "Choisissez parmi les résultats"
)



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
        tuple(prenoms_selectionnes), zone_selectionnee,
        periode_selectionnee[0], periode_selectionnee[1]
    )

    titre = "Évolution de : " + ", ".join(prenoms_selectionnes)
    if zone_selectionnee:
        titre += f" — {zone_selectionnee}"
    st.subheader(titre)
    st.line_chart(df_pivot)
else:
    #st.info("Sélectionnez un ou plusieurs prénoms dans la barre latérale pour commencer.") #Mauvaise couleur par rapport au thème
    st.markdown(
    """
    <div style="
        background-color: #EFE6D8;
        color: #3B2F2A;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #8B5E3C;
    ">
        Sélectionnez un ou plusieurs prénoms dans la barre latérale pour commencer.
    </div>
    """,
    unsafe_allow_html=True
    )

# ============ ZONE CENTRALE : CARTE ============
if prenoms_selectionnes:
    prenom_carte = prenoms_selectionnes[0]
    df_carte = preparer_donnees_carte(prenom_carte, annee_carte)

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
        scope="europe", title=f"Naissances de {prenom_carte} en {annee_carte} par département",
        hover_data={"valeur": True, "valeur_log": False},
        labels={colonne_couleur: titre_legende}
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # fond de toute la figure (zone autour du graphique)
        plot_bgcolor="rgba(0,0,0,0)",   # fond de la zone de tracé elle-même
        geo=dict(bgcolor="rgba(0,0,0,0)")  # fond spécifique à la carte géographique
    )
    st.plotly_chart(fig)

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

