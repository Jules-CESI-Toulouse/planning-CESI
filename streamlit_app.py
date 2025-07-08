import streamlit as st
from datetime import datetime, time, date
import pandas as pd
import json
import os
from PIL import Image
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Planification École d'Ingénieurs",
    page_icon="📚",
    layout="wide"
)

# Chargement du logo (à remplacer par votre propre logo)
try:
    logo = Image.open('logo.png')
    st.sidebar.image(logo, width=200)
except:
    st.sidebar.title("École d'Ingénieurs")

# Fonctions utilitaires
def charger_donnees():
    if os.path.exists('data/sauvegardes.json'):
        with open('data/sauvegardes.json', 'r') as f:
            return json.load(f)
    return {
        "enseignants": [],
        "sessions": [],
        "seances": [],
        "promotions": [],
        "groupes": []
    }

def sauvegarder_donnees(data):
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data/sauvegardes.json', 'w') as f:
        json.dump(data, f)

def afficher_calendrier(seances, date_debut, date_fin):
    df = pd.DataFrame(seances)
    df['Date'] = pd.to_datetime(df['date'])
    df = df[(df['Date'] >= date_debut) & (df['Date'] <= date_fin)]
    
    if not df.empty:
        df['Début'] = df['creneau'].apply(lambda x: "08:00" if "matin" in x else "14:00")
        df['Fin'] = df['Début'].apply(lambda x: "12:00" if x == "08:00" else "18:00")
        
        fig = px.timeline(
            df, 
            x_start="Début", 
            x_end="Fin", 
            y="groupe", 
            color="enseignant",
            title="Emploi du temps",
            hover_name="matiere",
            hover_data=["promotion", "session", "cout"]
        )
        fig.update_yaxes(title='Groupe')
        fig.update_xaxes(title='Heure')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune séance planifiée pour cette période.")

# Interface principale
def main():
    data = charger_donnees()
    
    st.sidebar.title("Navigation")
    onglet = st.sidebar.radio("", ["Accueil", "Enseignants", "Sessions", "Promotions", "Groupes", "Séances", "Budget", "Export"])
    
    # Onglet Accueil
    if onglet == "Accueil":
        st.title("Planification École d'Ingénieurs")
        st.write("""
        Bienvenue dans l'outil de planification pour l'école d'ingénieurs.
        Utilisez le menu de gauche pour naviguer entre les différentes fonctionnalités.
        """)
        
        # Affichage du calendrier pour la semaine en cours
        aujourdhui = datetime.now().date()
        debut_semaine = aujourdhui
        fin_semaine = aujourdhui + pd.Timedelta(days=7)
        
        st.subheader("Emploi du temps de la semaine")
        afficher_calendrier(data["seances"], debut_semaine, fin_semaine)
        
        # Statistiques rapides
        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre d'enseignants", len(data["enseignants"]))
        col2.metric("Nombre de séances", len(data["seances"]))
        col3.metric("Budget total", f"{sum(float(s['cout']) for s in data['seances']} €")
    
    # Onglet Enseignants
    elif onglet == "Enseignants":
        st.title("Gestion des enseignants")
        
        with st.expander("Ajouter un enseignant"):
            with st.form("form_enseignant"):
                nom = st.text_input("Nom")
                prenom = st.text_input("Prénom")
                tarif = st.number_input("Tarif horaire (€)", min_value=0.0, step=0.5)
                
                if st.form_submit_button("Ajouter"):
                    data["enseignants"].append({
                        "id": len(data["enseignants"]) + 1,
                        "nom": nom,
                        "prenom": prenom,
                        "tarif": tarif
                    })
                    sauvegarder_donnees(data)
                    st.success("Enseignant ajouté avec succès!")
        
        st.subheader("Liste des enseignants")
        if data["enseignants"]:
            df_enseignants = pd.DataFrame(data["enseignants"])
            st.dataframe(df_enseignants)
        else:
            st.info("Aucun enseignant enregistré.")
    
    # Onglet Sessions
    elif onglet == "Sessions":
        st.title("Gestion des sessions")
        
        with st.expander("Ajouter une session"):
            with st.form("form_session"):
                nom = st.text_input("Nom de la session")
                annee = st.number_input("Année", min_value=2023, max_value=2030, step=1)
                
                if st.form_submit_button("Ajouter"):
                    data["sessions"].append({
                        "id": len(data["sessions"]) + 1,
                        "nom": nom,
                        "annee": annee
                    })
                    sauvegarder_donnees(data)
                    st.success("Session ajoutée avec succès!")
        
        st.subheader("Liste des sessions")
        if data["sessions"]:
            df_sessions = pd.DataFrame(data["sessions"])
            st.dataframe(df_sessions)
        else:
            st.info("Aucune session enregistrée.")
    
    # Onglet Promotions
    elif onglet == "Promotions":
        st.title("Gestion des promotions")
        
        with st.expander("Ajouter une promotion"):
            with st.form("form_promo"):
                nom = st.text_input("Nom de la promotion")
                session_id = st.selectbox(
                    "Session",
                    options=[(s["id"], s["nom"]) for s in data["sessions"]],
                    format_func=lambda x: x[1]
                )
                
                if st.form_submit_button("Ajouter"):
                    data["promotions"].append({
                        "id": len(data["promotions"]) + 1,
                        "nom": nom,
                        "session_id": session_id[0]
                    })
                    sauvegarder_donnees(data)
                    st.success("Promotion ajoutée avec succès!")
        
        st.subheader("Liste des promotions")
        if data["promotions"]:
            df_promos = pd.DataFrame(data["promotions"])
            # Ajout du nom de la session pour plus de clarté
            sessions_dict = {s["id"]: s["nom"] for s in data["sessions"]}
            df_promos["session"] = df_promos["session_id"].map(sessions_dict)
            st.dataframe(df_promos[["id", "nom", "session"]])
        else:
            st.info("Aucune promotion enregistrée.")
    
    # Onglet Groupes
    elif onglet == "Groupes":
        st.title("Gestion des groupes")
        
        with st.expander("Ajouter un groupe"):
            with st.form("form_groupe"):
                nom = st.text_input("Nom du groupe")
                promo_id = st.selectbox(
                    "Promotion",
                    options=[(p["id"], p["nom"]) for p in data["promotions"]],
                    format_func=lambda x: x[1]
                )
                
                if st.form_submit_button("Ajouter"):
                    data["groupes"].append({
                        "id": len(data["groupes"]) + 1,
                        "nom": nom,
                        "promo_id": promo_id[0]
                    })
                    sauvegarder_donnees(data)
                    st.success("Groupe ajouté avec succès!")
        
        st.subheader("Liste des groupes")
        if data["groupes"]:
            df_groupes = pd.DataFrame(data["groupes"])
            # Ajout du nom de la promotion pour plus de clarté
            promos_dict = {p["id"]: p["nom"] for p in data["promotions"]}
            df_groupes["promotion"] = df_groupes["promo_id"].map(promos_dict)
            st.dataframe(df_groupes[["id", "nom", "promotion"]])
        else:
            st.info("Aucun groupe enregistré.")
    
    # Onglet Séances
    elif onglet == "Séances":
        st.title("Gestion des séances")
        
        # Calendrier interactif
        st.subheader("Calendrier interactif")
        
        col1, col2 = st.columns(2)
        with col1:
            date_seance = st.date_input("Date de la séance", min_value=date.today())
        with col2:
            creneau = st.selectbox(
                "Créneau horaire",
                options=["Matin (4h)", "Matin 1 (2h)", "Matin 2 (2h)", "Soir (4h)", "Soir 1 (2h)", "Soir 2 (2h)"]
            )
        
        # Calcul de la durée en fonction du créneau
        if "4h" in creneau:
            duree = 4
        else:
            duree = 2
        
        # Sélection du groupe
        groupe_id = st.selectbox(
            "Groupe",
            options=[(g["id"], g["nom"]) for g in data["groupes"]],
            format_func=lambda x: f"{x[1]} (Promo: {promos_dict.get(next((gr['promo_id'] for gr in data['groupes'] if gr['id'] == x[0]), ''))})"
        )
        
        # Sélection de l'enseignant
        enseignant_id = st.selectbox(
            "Enseignant",
            options=[(e["id"], f"{e['prenom']} {e['nom']}") for e in data["enseignants"]],
            format_func=lambda x: x[1]
        )
        
        matiere = st.text_input("Matière")
        
        if st.button("Ajouter la séance"):
            # Trouver le tarif de l'enseignant
            tarif = next((e["tarif"] for e in data["enseignants"] if e["id"] == enseignant_id[0]), 0)
            cout = duree * tarif
            
            # Trouver la promotion du groupe
            promo_id = next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None)
            session_id = next((p["session_id"] for p in data["promotions"] if p["id"] == promo_id), None)
            
            data["seances"].append({
                "id": len(data["seances"]) + 1,
                "date": str(date_seance),
                "creneau": creneau,
                "duree": duree,
                "groupe": groupe_id[1],
                "groupe_id": groupe_id[0],
                "promotion": promos_dict.get(promo_id, ""),
                "promo_id": promo_id,
                "session": sessions_dict.get(session_id, ""),
                "session_id": session_id,
                "enseignant": next((e[1] for e in [(e["id"], f"{e['prenom']} {e['nom']}") for e in data["enseignants"]] if e[0] == enseignant_id[0]), ""),
                "enseignant_id": enseignant_id[0],
                "matiere": matiere,
                "tarif": tarif,
                "cout": cout
            })
            sauvegarder_donnees(data)
            st.success("Séance ajoutée avec succès!")
        
        st.subheader("Séances planifiées")
        if data["seances"]:
            df_seances = pd.DataFrame(data["seances"])
            st.dataframe(df_seances[["date", "creneau", "matiere", "groupe", "promotion", "enseignant", "cout"]])
        else:
            st.info("Aucune séance planifiée.")
    
    # Onglet Budget
    elif onglet == "Budget":
        st.title("Analyse budgétaire")
        
        if not data["seances"]:
            st.info("Aucune séance planifiée pour analyser le budget.")
        else:
            df_seances = pd.DataFrame(data["seances"])
            
            st.subheader("Budget par enseignant")
            budget_enseignant = df_seances.groupby("enseignant")["cout"].sum().reset_index()
            fig1 = px.bar(budget_enseignant, x="enseignant", y="cout", title="Budget par enseignant")
            st.plotly_chart(fig1, use_container_width=True)
            
            st.subheader("Budget par promotion")
            budget_promo = df_seances.groupby("promotion")["cout"].sum().reset_index()
            fig2 = px.pie(budget_promo, values="cout", names="promotion", title="Répartition par promotion")
            st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("Budget total")
            total = df_seances["cout"].sum()
            st.metric("Coût total des séances", f"{total:.2f} €")
    
    # Onglet Export
    elif onglet == "Export":
        st.title("Exporter les données")
        
        if st.button("Exporter vers Excel"):
            with pd.ExcelWriter('export_planification.xlsx') as writer:
                if data["enseignants"]:
                    pd.DataFrame(data["enseignants"]).to_excel(writer, sheet_name="Enseignants", index=False)
                if data["sessions"]:
                    pd.DataFrame(data["sessions"]).to_excel(writer, sheet_name="Sessions", index=False)
                if data["promotions"]:
                    pd.DataFrame(data["promotions"]).to_excel(writer, sheet_name="Promotions", index=False)
                if data["groupes"]:
                    pd.DataFrame(data["groupes"]).to_excel(writer, sheet_name="Groupes", index=False)
                if data["seances"]:
                    pd.DataFrame(data["seances"]).to_excel(writer, sheet_name="Séances", index=False)
            
            with open('export_planification.xlsx', 'rb') as f:
                st.download_button(
                    label="Télécharger le fichier Excel",
                    data=f,
                    file_name='export_planification.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        
        st.subheader("Sauvegarde/restauration")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Sauvegarder les données actuelles")
            if st.button("Télécharger la sauvegarde"):
                with open('data/sauvegardes.json', 'r') as f:
                    st.download_button(
                        label="Télécharger",
                        data=f,
                        file_name='sauvegarde_planification.json',
                        mime='application/json'
                    )
        
        with col2:
            st.write("Restaurer des données")
            fichier = st.file_uploader("Importer un fichier de sauvegarde", type=['json'])
            if fichier is not None:
                contenu = fichier.getvalue().decode('utf-8')
                try:
                    json.loads(contenu)  # Validation JSON
                    with open('data/sauvegardes.json', 'w') as f:
                        f.write(contenu)
                    st.success("Sauvegarde restaurée avec succès!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier: {e}")

if __name__ == "__main__":
    main()
