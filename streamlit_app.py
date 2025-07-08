import streamlit as st
from datetime import datetime, date
import pandas as pd
import json
import os
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Planification École d'Ingénieurs",
    page_icon="📚",
    layout="wide"
)

# Fonctions utilitaires
def charger_donnees():
    """Charge les données depuis le fichier de sauvegarde"""
    if os.path.exists('data/sauvegardes.json'):
        with open('data/sauvegardes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "enseignants": [],
        "sessions": [],
        "seances": [],
        "promotions": [],
        "groupes": []
    }

def sauvegarder_donnees(data):
    """Sauvegarde les données dans un fichier JSON"""
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data/sauvegardes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def afficher_calendrier(seances, date_debut, date_fin):
    """Affiche le calendrier des séances"""
    if not seances:
        st.warning("Aucune séance planifiée pour cette période.")
        return
    
    try:
        df = pd.DataFrame(seances)
        
        # Vérification des colonnes nécessaires
        if 'date' not in df.columns:
            st.error("Les données des séances ne contiennent pas de date.")
            return
            
        df['Date'] = pd.to_datetime(df['date'])
        df = df[(df['Date'] >= pd.to_datetime(date_debut)) & 
               (df['Date'] <= pd.to_datetime(date_fin))]
        
        if df.empty:
            st.warning("Aucune séance planifiée pour cette période.")
            return
        
        # Création des colonnes pour le calendrier
        df['Début'] = df['creneau'].apply(
            lambda x: "08:00" if "matin" in x.lower() else "14:00"
        )
        df['Fin'] = df['Début'].apply(
            lambda x: "12:00" if x == "08:00" else "18:00"
        )
        
        # Vérification et complétion des colonnes
        for col in ['groupe', 'enseignant', 'matiere', 'promotion', 'session', 'cout']:
            if col not in df.columns:
                df[col] = "Non spécifié"
        
        # Création du calendrier visuel
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
        
    except Exception as e:
        st.error(f"Erreur lors de la création du calendrier: {str(e)}")

# Interface principale
def main():
    data = charger_donnees()
    
    # Création des dictionnaires de référence
    sessions_dict = {s["id"]: s["nom"] for s in data["sessions"]} if data["sessions"] else {}
    promos_dict = {p["id"]: p["nom"] for p in data["promotions"]} if data["promotions"] else {}
    enseignants_dict = {e["id"]: f"{e['prenom']} {e['nom']}" for e in data["enseignants"]} if data["enseignants"] else {}
    groupes_promos = {g["id"]: promos_dict.get(g["promo_id"], "N/A") for g in data["groupes"]} if data["groupes"] else {}

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    onglet = st.sidebar.radio("Menu", [
        "Accueil", "Enseignants", "Sessions", 
        "Promotions", "Groupes", "Séances", 
        "Budget", "Export"
    ])
    
    # Onglet Accueil
    if onglet == "Accueil":
        st.title("Planification École d'Ingénieurs")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre d'enseignants", len(data["enseignants"]))
        col2.metric("Nombre de séances", len(data["seances"]))
        
        total = sum(float(s.get('cout', 0)) for s in data["seances"]) if data["seances"] else 0
        col3.metric("Budget total", f"{total:.2f} €")
        
        aujourdhui = date.today()
        debut_semaine = aujourdhui
        fin_semaine = aujourdhui + pd.Timedelta(days=7)
        
        st.subheader("Emploi du temps de la semaine")
        afficher_calendrier(data["seances"], debut_semaine, fin_semaine)
    
    # Onglet Enseignants
    elif onglet == "Enseignants":
        st.title("Gestion des enseignants")
        
        with st.expander("Ajouter un enseignant", expanded=True):
            with st.form("form_enseignant"):
                nom = st.text_input("Nom*", key="nom_enseignant")
                prenom = st.text_input("Prénom*", key="prenom_enseignant")
                tarif = st.number_input("Tarif horaire (€)*", min_value=0.0, step=0.5, key="tarif_enseignant")
                
                if st.form_submit_button("Ajouter l'enseignant"):
                    if nom and prenom:
                        data["enseignants"].append({
                            "id": max([e["id"] for e in data["enseignants"]], default=0) + 1,
                            "nom": nom,
                            "prenom": prenom,
                            "tarif": float(tarif)
                        })
                        sauvegarder_donnees(data)
                        st.success("Enseignant ajouté avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Les champs marqués d'un * sont obligatoires")
        
        if data["enseignants"]:
            st.subheader("Liste des enseignants")
            df_enseignants = pd.DataFrame(data["enseignants"])
            st.dataframe(df_enseignants[["nom", "prenom", "tarif"]])
        else:
            st.info("Aucun enseignant enregistré.")
    
    # Onglet Sessions
    elif onglet == "Sessions":
        st.title("Gestion des sessions")
        
        with st.expander("Ajouter une session", expanded=True):
            with st.form("form_session"):
                nom = st.text_input("Nom de la session*", key="nom_session")
                annee = st.number_input("Année*", min_value=2023, max_value=2030, step=1, key="annee_session")
                
                if st.form_submit_button("Ajouter la session"):
                    if nom:
                        data["sessions"].append({
                            "id": max([s["id"] for s in data["sessions"]], default=0) + 1,
                            "nom": nom,
                            "annee": int(annee)
                        })
                        sauvegarder_donnees(data)
                        st.success("Session ajoutée avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Le nom de la session est obligatoire")
        
        if data["sessions"]:
            st.subheader("Liste des sessions")
            df_sessions = pd.DataFrame(data["sessions"])
            st.dataframe(df_sessions[["nom", "annee"]])
        else:
            st.info("Aucune session enregistrée.")
    
    # Onglet Promotions
    elif onglet == "Promotions":
        st.title("Gestion des promotions")
        
        with st.expander("Ajouter une promotion", expanded=True):
            with st.form("form_promo"):
                nom = st.text_input("Nom de la promotion*", key="nom_promo")
                session_id = st.selectbox(
                    "Session*",
                    options=[(s["id"], s["nom"]) for s in data["sessions"]],
                    format_func=lambda x: x[1],
                    key="session_promo"
                ) if data["sessions"] else None
                
                if st.form_submit_button("Ajouter la promotion") and session_id:
                    if nom:
                        data["promotions"].append({
                            "id": max([p["id"] for p in data["promotions"]], default=0) + 1,
                            "nom": nom,
                            "session_id": session_id[0]
                        })
                        sauvegarder_donnees(data)
                        st.success("Promotion ajoutée avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Le nom de la promotion est obligatoire")
                elif not data["sessions"]:
                    st.error("Veuillez d'abord créer une session")
        
        if data["promotions"]:
            st.subheader("Liste des promotions")
            df_promos = pd.DataFrame(data["promotions"])
            df_promos["session"] = df_promos["session_id"].map(sessions_dict)
            st.dataframe(df_promos[["nom", "session"]])
        else:
            st.info("Aucune promotion enregistrée.")
    
    # Onglet Groupes
    elif onglet == "Groupes":
        st.title("Gestion des groupes")
        
        with st.expander("Ajouter un groupe", expanded=True):
            with st.form("form_groupe"):
                nom = st.text_input("Nom du groupe*", key="nom_groupe")
                promo_id = st.selectbox(
                    "Promotion*",
                    options=[(p["id"], p["nom"]) for p in data["promotions"]],
                    format_func=lambda x: x[1],
                    key="promo_groupe"
                ) if data["promotions"] else None
                
                if st.form_submit_button("Ajouter le groupe") and promo_id:
                    if nom:
                        data["groupes"].append({
                            "id": max([g["id"] for g in data["groupes"]], default=0) + 1,
                            "nom": nom,
                            "promo_id": promo_id[0]
                        })
                        sauvegarder_donnees(data)
                        st.success("Groupe ajouté avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Le nom du groupe est obligatoire")
                elif not data["promotions"]:
                    st.error("Veuillez d'abord créer une promotion")
        
        if data["groupes"]:
            st.subheader("Liste des groupes")
            df_groupes = pd.DataFrame(data["groupes"])
            df_groupes["promotion"] = df_groupes["promo_id"].map(promos_dict)
            st.dataframe(df_groupes[["nom", "promotion"]])
        else:
            st.info("Aucun groupe enregistré.")
    
    # Onglet Séances
    elif onglet == "Séances":
        st.title("Planification des séances")
        
        if not data["groupes"] or not data["enseignants"]:
            st.warning("Veuillez d'abord créer des groupes et des enseignants")
        else:
            # Sélection de la date et du créneau
            col1, col2 = st.columns(2)
            with col1:
                date_seance = st.date_input("Date de la séance*", min_value=date.today(), key="date_seance")
            with col2:
                creneau = st.selectbox(
                    "Créneau horaire*",
                    options=["Matin (4h)", "Matin 1 (2h)", "Matin 2 (2h)", 
                            "Soir (4h)", "Soir 1 (2h)", "Soir 2 (2h)"],
                    key="creneau_seance"
                )
            
            # Calcul de la durée
            duree = 4 if "4h" in creneau else 2
            
            # Sélection du groupe
            groupe_options = [(g["id"], g["nom"]) for g in data["groupes"]]
            groupe_id = st.selectbox(
                "Groupe*",
                options=groupe_options,
                format_func=lambda x: f"{x[1]} (Promo: {groupes_promos.get(x[0], 'N/A')})",
                key="groupe_seance"
            )
            
            # Sélection de l'enseignant
            enseignant_options = [(e["id"], f"{e['prenom']} {e['nom']}") for e in data["enseignants"]]
            enseignant_id = st.selectbox(
                "Enseignant*",
                options=enseignant_options,
                format_func=lambda x: x[1],
                key="enseignant_seance"
            )
            
            # Matière
            matiere = st.text_input("Matière*", key="matiere_seance")
            
            if st.button("Planifier la séance", key="ajouter_seance"):
                if matiere:
                    try:
                        # Calcul du coût
                        tarif = next((float(e["tarif"]) for e in data["enseignants"] if e["id"] == enseignant_id[0]), 0)
                        cout = duree * tarif
                        
                        # Création de la séance
                        nouvelle_seance = {
                            "id": max([s["id"] for s in data["seances"]], default=0) + 1,
                            "date": date_seance.isoformat(),
                            "creneau": creneau,
                            "duree": duree,
                            "groupe": groupe_id[1],
                            "groupe_id": groupe_id[0],
                            "promotion": groupes_promos.get(groupe_id[0], "N/A"),
                            "promo_id": next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None),
                            "session": sessions_dict.get(next((p["session_id"] for p in data["promotions"] if p["id"] == next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None)), None), "N/A"),
                            "session_id": next((p["session_id"] for p in data["promotions"] if p["id"] == next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None)), None),
                            "enseignant": enseignant_id[1],
                            "enseignant_id": enseignant_id[0],
                            "matiere": matiere,
                            "tarif": tarif,
                            "cout": cout
                        }
                        
                        data["seances"].append(nouvelle_seance)
                        sauvegarder_donnees(data)
                        st.success("Séance planifiée avec succès!")
                        st.experimental_rerun()
                    
                    except Exception as e:
                        st.error(f"Erreur lors de la planification: {str(e)}")
                else:
                    st.error("La matière est obligatoire")
            
            # Affichage des séances planifiées
            st.subheader("Séances planifiées")
            if data["seances"]:
                df_seances = pd.DataFrame(data["seances"])
                df_seances["date"] = pd.to_datetime(df_seances["date"]).dt.date
                st.dataframe(
                    df_seances[["date", "creneau", "matiere", "groupe", "promotion", "enseignant", "cout"]],
                    column_config={
                        "date": "Date",
                        "creneau": "Créneau",
                        "matiere": "Matière",
                        "groupe": "Groupe",
                        "promotion": "Promotion",
                        "enseignant": "Enseignant",
                        "cout": st.column_config.NumberColumn("Coût (€)", format="%.2f €")
                    }
                )
            else:
                st.info("Aucune séance planifiée.")
    
    # Onglet Budget
    elif onglet == "Budget":
        st.title("Analyse budgétaire")
        
        if not data["seances"]:
            st.info("Aucune séance planifiée pour analyser le budget.")
        else:
            df_seances = pd.DataFrame(data["seances"])
            
            # Budget par enseignant
            st.subheader("Budget par enseignant")
            budget_enseignant = df_seances.groupby("enseignant")["cout"].sum().reset_index()
            fig1 = px.bar(
                budget_enseignant, 
                x="enseignant", 
                y="cout", 
                title="Budget par enseignant",
                labels={"enseignant": "Enseignant", "cout": "Coût (€)"}
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Budget par promotion
            st.subheader("Budget par promotion")
            if "promotion" in df_seances.columns:
                budget_promo = df_seances.groupby("promotion")["cout"].sum().reset_index()
                fig2 = px.pie(
                    budget_promo, 
                    values="cout", 
                    names="promotion", 
                    title="Répartition par promotion",
                    labels={"promotion": "Promotion", "cout": "Coût (€)"}
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Données de promotion manquantes pour l'analyse")
            
            # Budget total
            st.subheader("Budget total")
            total = df_seances["cout"].sum()
            st.metric("Coût total des séances", f"{total:.2f} €")
    
    # Onglet Export
    elif onglet == "Export":
        st.title("Exporter les données")
        
        # Export Excel
        st.subheader("Export Excel")
        if st.button("Générer le fichier Excel"):
            try:
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
            except Exception as e:
                st.error(f"Erreur lors de l'export Excel: {str(e)}")
        
        # Sauvegarde/Restauration
        st.subheader("Sauvegarde des données")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Télécharger une sauvegarde complète")
            if st.button("Générer la sauvegarde"):
                with open('data/sauvegardes.json', 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="Télécharger la sauvegarde",
                        data=f,
                        file_name='sauvegarde_planification.json',
                        mime='application/json'
                    )
        
        with col2:
            st.write("Restaurer une sauvegarde")
            fichier = st.file_uploader("Importer un fichier JSON", type=['json'])
            if fichier is not None:
                try:
                    contenu = fichier.getvalue().decode('utf-8')
                    json.loads(contenu)  # Validation JSON
                    with open('data/sauvegardes.json', 'w', encoding='utf-8') as f:
                        f.write(contenu)
                    st.success("Sauvegarde restaurée avec succès!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la restauration: {str(e)}")

if __name__ == "__main__":
    main()
