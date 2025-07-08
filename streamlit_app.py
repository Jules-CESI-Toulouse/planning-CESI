# planning_budget_tool.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Planification & Budget", layout="wide")
st.title("🗓️ Outil de Planification et de Budget pour Étudiants")

# ---------- Fonctions ----------
def save_data(data):
    json_str = json.dumps(data, indent=2, default=str)
    st.download_button("💾 Télécharger la sauvegarde", data=json_str, file_name="sauvegarde_planning.json")

def load_data():
    uploaded_file = st.file_uploader("📤 Charger une sauvegarde", type=["json"])
    if uploaded_file:
        return json.load(uploaded_file)
    return None

def calculer_cout(heure, tarif):
    return heure * tarif

def export_excel(seances):
    output = BytesIO()
    df = pd.DataFrame(seances)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Séances')
    output.seek(0)
    st.download_button("📥 Exporter en Excel", data=output, file_name="planning.xlsx")

# ---------- Initialisation ou chargement ----------
data = load_data() or {
    "sessions": [],
    "enseignants": [],
    "seances": []
}

# ---------- Interface Enseignants ----------
st.header("👨‍🏫 Gestion des enseignants")
nom_ens = st.text_input("Nom de l'enseignant")
tarif_ens = st.number_input("Tarif horaire (€)", min_value=0.0, format="%.2f")
if st.button("Ajouter l'enseignant"):
    data["enseignants"].append({"nom": nom_ens, "tarif": tarif_ens})

if data["enseignants"]:
    df_ens = pd.DataFrame(data["enseignants"])
    st.dataframe(df_ens)

# ---------- Interface Sessions / Promos / Groupes ----------
st.header("🏫 Sessions, Promos et Groupes")
session_nom = st.text_input("Nom de la session")
if st.button("Créer une session"):
    data["sessions"].append({"nom": session_nom, "promos": []})

for session in data["sessions"]:
    st.subheader(f"Session : {session['nom']}")
    promo_nom = st.text_input(f"Ajouter une promo à {session['nom']}", key=session['nom'])
    if st.button(f"Ajouter promo à {session['nom']}", key=f"btn_{session['nom']}"):
        session["promos"].append({"nom": promo_nom, "groupes": []})

    for promo in session["promos"]:
        st.markdown(f"**Promo : {promo['nom']}**")
        groupe_nom = st.text_input(f"Ajouter un groupe à {promo['nom']}", key=promo['nom'])
        if st.button(f"Ajouter groupe à {promo['nom']}", key=f"btn_{promo['nom']}"):
            promo["groupes"].append(groupe_nom)
        if promo['groupes']:
            st.write(f"Groupes : {', '.join(promo['groupes'])}")

# ---------- Interface Séances ----------
st.header("🕘 Planification des séances")
if not data["enseignants"]:
    st.warning("Ajoutez d'abord des enseignants.")
else:
    enseignant_sel = st.selectbox("Choisir un enseignant", options=[e["nom"] for e in data["enseignants"]])
    date_seance = st.date_input("Date de la séance")
    tranche = st.selectbox("Tranche horaire", ["Matin (4h)", "Matin 1 (2h)", "Matin 2 (2h)", "Soir (4h)", "Soir 1 (2h)", "Soir 2 (2h)"])

    session_liste = [s["nom"] for s in data["sessions"]]
    session_choisie = st.selectbox("Session concernée", session_liste)
    promo_liste = []
    groupe_liste = []
    for s in data["sessions"]:
        if s["nom"] == session_choisie:
            promo_liste = [p["nom"] for p in s["promos"]]
            break
    promo_choisie = st.selectbox("Promo", promo_liste)
    for s in data["sessions"]:
        if s["nom"] == session_choisie:
            for p in s["promos"]:
                if p["nom"] == promo_choisie:
                    groupe_liste = p["groupes"]
                    break
    groupe_choisi = st.selectbox("Groupe", groupe_liste)

    duree_map = {
        "Matin (4h)": 4,
        "Matin 1 (2h)": 2,
        "Matin 2 (2h)": 2,
        "Soir (4h)": 4,
        "Soir 1 (2h)": 2,
        "Soir 2 (2h)": 2
    }
    duree = duree_map[tranche]
    tarif_horaire = next(e["tarif"] for e in data["enseignants"] if e["nom"] == enseignant_sel)
    cout = calculer_cout(duree, tarif_horaire)
    if st.button("Ajouter la séance"):
        data["seances"].append({
            "enseignant": enseignant_sel,
            "date": str(date_seance),
            "tranche": tranche,
            "duree": duree,
            "tarif_horaire": tarif_horaire,
            "cout": cout,
            "session": session_choisie,
            "promo": promo_choisie,
            "groupe": groupe_choisi
        })

    if data["seances"]:
        df_seances = pd.DataFrame(data["seances"])
        st.subheader("📋 Séances enregistrées")
        st.dataframe(df_seances)
        total = df_seances["cout"].sum()
        st.success(f"💰 Coût total : {total:.2f} €")
        export_excel(data["seances"])

        # ---------- Affichage graphique du planning ----------
        st.header("📆 Emploi du temps - Vue graphique")

        df_seances['datetime'] = pd.to_datetime(df_seances['date'])
        df_seances = df_seances.sort_values(by='datetime')

        # Plage de dates pour filtrage temporel
        dates_unique = df_seances['datetime'].sort_values().unique()
        date_min = dates_unique.min()
        date_max = dates_unique.max()
        plage = st.date_input("Filtrer par période", value=(date_min, date_max))
        if isinstance(plage, tuple) and len(plage) == 2:
            df_seances = df_seances[
                (df_seances['datetime'] >= pd.to_datetime(plage[0])) &
                (df_seances['datetime'] <= pd.to_datetime(plage[1]))
            ]

        # Filtres dynamiques
        st.markdown("### 🔍 Filtres")
        enseignant_filter = st.multiselect("Filtrer par enseignant", df_seances["enseignant"].unique())
        promo_filter = st.multiselect("Filtrer par promo", df_seances["promo"].unique())
        groupe_filter = st.multiselect("Filtrer par groupe", df_seances["groupe"].unique())

        if enseignant_filter:
            df_seances = df_seances[df_seances["enseignant"].isin(enseignant_filter)]
        if promo_filter:
            df_seances = df_seances[df_seances["promo"].isin(promo_filter)]
        if groupe_filter:
            df_seances = df_seances[df_seances["groupe"].isin(groupe_filter)]

        # Transformation pour affichage
        df_plot = df_seances.copy()
        df_plot['heure_debut'] = df_plot['tranche'].map({
            "Matin (4h)": 8,
            "Matin 1 (2h)": 8,
            "Matin 2 (2h)": 10,
            "Soir (4h)": 14,
            "Soir 1 (2h)": 14,
            "Soir 2 (2h)": 16
        })
        df_plot['start'] = pd.to_datetime(df_plot['date']) + pd.to_timedelta(df_plot['heure_debut'], unit='h')
        df_plot['end'] = df_plot['start'] + pd.to_timedelta(df_plot['duree'], unit='h')
        df_plot['titre'] = df_plot['enseignant'] + " - " + df_plot['groupe']

        fig = px.timeline(
            df_plot,
            x_start="start",
            x_end="end",
            y="promo",
            color="enseignant",
            text="titre",
            title="Emploi du temps - Séances programmées"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# ---------- Sauvegarde ----------
st.header("💾 Sauvegarde")
save_data(data)
