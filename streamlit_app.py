import streamlit as st
from datetime import datetime, date, timedelta
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

def get_jour_semaine(date_obj):
    """Retourne le jour de la semaine en français"""
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return jours[date_obj.weekday()]

def get_heure_debut(creneau):
    """Retourne l'heure de début en fonction du créneau"""
    if "matin" in creneau.lower():
        return datetime.strptime("08:00", "%H:%M") if "1" in creneau or "4h" in creneau else datetime.strptime("10:00", "%H:%M")
    else:
        return datetime.strptime("14:00", "%H:%M") if "1" in creneau or "4h" in creneau else datetime.strptime("16:00", "%H:%M")

def get_heure_fin(creneau):
    """Retourne l'heure de fin en fonction du créneau"""
    if "matin" in creneau.lower():
        return datetime.strptime("10:00", "%H:%M") if "1" in creneau else datetime.strptime("12:00", "%H:%M")
    else:
        return datetime.strptime("16:00", "%H:%M") if "1" in creneau else datetime.strptime("18:00", "%H:%M")

def afficher_calendrier_semaine(seances, date_debut):
    """Affiche un calendrier semaine interactif"""
    date_fin = date_debut + timedelta(days=6)

    # Création du DataFrame
    df = pd.DataFrame(seances)
    if df.empty:
        st.warning("Aucune séance planifiée pour cette semaine")
        return

    # Conversion des dates
    df['Date'] = pd.to_datetime(df['date'])
    df = df[(df['Date'] >= pd.to_datetime(date_debut)) & (df['Date'] <= pd.to_datetime(date_fin))]

    if df.empty:
        st.warning("Aucune séance planifiée pour cette semaine")
        return

    # Préparation des données pour le calendrier
    df['Jour'] = df['Date'].apply(lambda x: get_jour_semaine(x.date()))
    df['Début'] = df['creneau'].apply(lambda x: get_heure_debut(x))
    df['Fin'] = df['creneau'].apply(lambda x: get_heure_fin(x))

    # Tri des jours de la semaine
    jours_ordre = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    df['Jour'] = pd.Categorical(df['Jour'], categories=jours_ordre, ordered=True)
    df = df.sort_values(['Jour', 'Début'])

    # Création du calendrier
    fig = px.timeline(
        df,
        x_start="Début",
        x_end="Fin",
        y="Jour",
        color="enseignant",
        hover_name="matiere",
        hover_data=["groupe", "promotion", "cout"],
        title=f"Emploi du temps - Semaine du {date_debut.strftime('%d/%m/%Y')}",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    # Personnalisation du calendrier
    fig.update_yaxes(title='', categoryorder='array', categoryarray=jours_ordre)
    fig.update_xaxes(
        title='',
        tickformat="%H:%M",
        range=[get_heure_debut("Matin 1 (2h)"), get_heure_fin("Soir 2 (2h)")]
    )
    fig.update_layout(
        height=600,
        showlegend=True,
        legend_title_text='Enseignants'
    )

    st.plotly_chart(fig, use_container_width=True)

def afficher_formulaire_seance(data, edit_id=None):
    """Affiche le formulaire d'ajout/modification de séance"""
    with st.form("form_seance", clear_on_submit=edit_id is None):
        # Sélection de la date et du créneau
        col1, col2 = st.columns(2)
        with col1:
            date_seance = st.date_input("Date*", value=date.today())
        with col2:
            creneau = st.selectbox(
                "Créneau horaire*",
                options=["Matin (4h)", "Matin 1 (2h)", "Matin 2 (2h)",
                        "Soir (4h)", "Soir 1 (2h)", "Soir 2 (2h)"]
            )

        # Sélection du groupe
        groupe_options = [(g["id"], g["nom"]) for g in data["groupes"]]
        groupe_id = st.selectbox(
            "Groupe*",
            options=groupe_options,
            format_func=lambda x: f"{x[1]}",
            index=0
        )

        # Sélection de l'enseignant
        enseignant_options = [(e["id"], f"{e['prenom']} {e['nom']}") for e in data["enseignants"]]
        enseignant_id = st.selectbox(
            "Enseignant*",
            options=enseignant_options,
            format_func=lambda x: x[1],
            index=0
        )

        # Matière et boutons
        matiere = st.text_input("Matière*", value="")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Enregistrer"):
                if not matiere:
                    st.error("La matière est obligatoire")
                    return False

                # Calcul du coût
                tarif = next((float(e["tarif"]) for e in data["enseignants"] if e["id"] == enseignant_id[0]), 0)
                cout = (4 if "4h" in creneau else 2) * tarif

                # Création/mise à jour de la séance
                nouvelle_seance = {
                    "id": edit_id if edit_id else max([s["id"] for s in data["seances"]], default=0) + 1,
                    "date": date_seance.isoformat(),
                    "creneau": creneau,
                    "duree": 4 if "4h" in creneau else 2,
                    "groupe": groupe_id[1],
                    "groupe_id": groupe_id[0],
                    "promotion": next((p["nom"] for p in data["promotions"] if p["id"] == next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None)), "N/A"),
                    "promo_id": next((g["promo_id"] for g in data["groupes"] if g["id"] == groupe_id[0]), None),
                    "enseignant": enseignant_id[1],
                    "enseignant_id": enseignant_id[0],
                    "matiere": matiere,
                    "tarif": tarif,
                    "cout": cout
                }

                if edit_id:
                    # Mise à jour de la séance existante
                    for i, s in enumerate(data["seances"]):
                        if s["id"] == edit_id:
                            data["seances"][i] = nouvelle_seance
                            break
                else:
                    # Ajout d'une nouvelle séance
                    data["seances"].append(nouvelle_seance)

                sauvegarder_donnees(data)
                st.success("Séance enregistrée avec succès!")
                return True

        with col2:
            if edit_id and st.form_submit_button("Annuler"):
                return True

    return False

def supprimer_element(data, element_type, element_id):
    """Supprime un élément de la base de données"""
    if element_type == "seance":
        data["seances"] = [s for s in data["seances"] if s["id"] != element_id]
    elif element_type == "enseignant":
        # Vérifier si l'enseignant a des séances planifiées
        seances_enseignant = [s for s in data["seances"] if s["enseignant_id"] == element_id]
        if seances_enseignant:
            st.error("Cet enseignant a des séances planifiées. Supprimez d'abord ses séances.")
            return False
        data["enseignants"] = [e for e in data["enseignants"] if e["id"] != element_id]
    elif element_type == "groupe":
        # Vérifier si le groupe a des séances planifiées
        seances_groupe = [s for s in data["seances"] if s["groupe_id"] == element_id]
        if seances_groupe:
            st.error("Ce groupe a des séances planifiées. Supprimez d'abord ses séances.")
            return False
        data["groupes"] = [g for g in data["groupes"] if g["id"] != element_id]
    elif element_type == "promotion":
        # Vérifier si la promotion a des groupes
        groupes_promo = [g for g in data["groupes"] if g["promo_id"] == element_id]
        if groupes_promo:
            st.error("Cette promotion a des groupes associés. Supprimez d'abord les groupes.")
            return False
        data["promotions"] = [p for p in data["promotions"] if p["id"] != element_id]
    elif element_type == "session":
        # Vérifier si la session a des promotions
        promotions_session = [p for p in data["promotions"] if p["session_id"] == element_id]
        if promotions_session:
            st.error("Cette session a des promotions associées. Supprimez d'abord les promotions.")
            return False
        data["sessions"] = [s for s in data["sessions"] if s["id"] != element_id]

    sauvegarder_donnees(data)
    return True

def afficher_budget_annuel(seances):
    """Affiche le budget par année civile"""
    if not seances:
        st.warning("Aucune séance planifiée pour analyser le budget.")
        return

    df = pd.DataFrame(seances)
    df['Date'] = pd.to_datetime(df['date'])
    df['Année'] = df['Date'].dt.year

    # Budget par année
    st.subheader("Budget par année civile")
    budget_annuel = df.groupby('Année')['cout'].sum().reset_index()

    if not budget_annuel.empty:
        fig = px.bar(
            budget_annuel,
            x='Année',
            y='cout',
            title='Budget par année',
            labels={'Année': 'Année', 'cout': 'Coût (€)'},
            text_auto='.2s'
        )
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

        # Affichage détaillé
        st.dataframe(
            budget_annuel,
            column_config={
                "Année": st.column_config.NumberColumn("Année", format="%d"),
                "cout": st.column_config.NumberColumn("Coût total (€)", format="%.2f €")
            },
            hide_index=True
        )
    else:
        st.info("Aucune donnée budgétaire disponible par année")

# Interface principale
def main():
    data = charger_donnees()

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    onglet = st.sidebar.radio("Menu", [
        "Calendrier", "Séances", "Enseignants",
        "Groupes", "Promotions", "Sessions",
        "Budget", "Export"
    ])

    # Onglet Calendrier
    if onglet == "Calendrier":
        st.title("Calendrier des séances")

        # Sélection de la semaine
        aujourdhui = date.today()
        debut_semaine = st.date_input(
            "Choisir une semaine",
            value=aujourdhui - timedelta(days=aujourdhui.weekday()),
            key="date_calendrier"
        )

        # Affichage du calendrier
        afficher_calendrier_semaine(data["seances"], debut_semaine)

        # Bouton pour ajouter une séance depuis le calendrier
        if st.button("Ajouter une séance", key="ajout_calendrier"):
            st.session_state["ajout_seance"] = True

        if st.session_state.get("ajout_seance", False):
            if afficher_formulaire_seance(data):
                st.session_state["ajout_seance"] = False
                st.experimental_rerun()

    # Onglet Séances
    elif onglet == "Séances":
        st.title("Gestion des séances")

        # Formulaire d'ajout
        with st.expander("Ajouter/Modifier une séance", expanded=True):
            edit_id = st.session_state.get("edit_seance_id", None)
            if afficher_formulaire_seance(data, edit_id):
                if "edit_seance_id" in st.session_state:
                    del st.session_state["edit_seance_id"]
                st.experimental_rerun()

        # Liste des séances avec actions
        st.subheader("Liste des séances")
        if data["seances"]:
            df = pd.DataFrame(data["seances"])
            df['date'] = pd.to_datetime(df['date']).dt.date

            # Affichage sous forme de tableau avec actions
            for _, row in df.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{row['date'].strftime('%d/%m/%Y')}** - {row['creneau']}")
                    st.write(f"{row['matiere']} avec {row['enseignant']} pour le groupe {row['groupe']}")
                    st.write(f"Coût: {row['cout']:.2f}€")

                with col2:
                    if st.button("✏️", key=f"edit_{row['id']}"):
                        st.session_state["edit_seance_id"] = row['id']
                        st.experimental_rerun()

                with col3:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        if supprimer_element(data, "seance", row['id']):
                            st.success("Séance supprimée avec succès!")
                            st.experimental_rerun()

                st.divider()
        else:
            st.info("Aucune séance planifiée")

    # Onglet Enseignants
    elif onglet == "Enseignants":
        st.title("Gestion des enseignants")

        # Formulaire d'ajout/modification
        with st.expander("Ajouter/Modifier un enseignant", expanded=True):
            edit_id = st.session_state.get("edit_enseignant_id", None)
            enseignant = next((e for e in data["enseignants"] if e["id"] == edit_id), None) if edit_id else None

            with st.form("form_enseignant"):
                nom = st.text_input("Nom*", value=enseignant["nom"] if enseignant else "")
                prenom = st.text_input("Prénom*", value=enseignant["prenom"] if enseignant else "")
                tarif = st.number_input(
                    "Tarif horaire (€)*",
                    min_value=0.0,
                    step=0.5,
                    value=float(enseignant["tarif"]) if enseignant else 0.0
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Enregistrer"):
                        if not nom or not prenom:
                            st.error("Les champs marqués d'un * sont obligatoires")
                        else:
                            if edit_id:
                                # Mise à jour
                                for e in data["enseignants"]:
                                    if e["id"] == edit_id:
                                        e.update({
                                            "nom": nom,
                                            "prenom": prenom,
                                            "tarif": tarif
                                        })
                                        break
                            else:
                                # Ajout
                                data["enseignants"].append({
                                    "id": max([e["id"] for e in data["enseignants"]], default=0) + 1,
                                    "nom": nom,
                                    "prenom": prenom,
                                    "tarif": tarif
                                })

                            sauvegarder_donnees(data)
                            st.success("Enseignant enregistré avec succès!")
                            if "edit_enseignant_id" in st.session_state:
                                del st.session_state["edit_enseignant_id"]
                            st.experimental_rerun()

                with col2:
                    if edit_id and st.form_submit_button("Annuler"):
                        if "edit_enseignant_id" in st.session_state:
                            del st.session_state["edit_enseignant_id"]
                        st.experimental_rerun()

        # Liste des enseignants avec actions
        st.subheader("Liste des enseignants")
        if data["enseignants"]:
            for enseignant in data["enseignants"]:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{enseignant['prenom']} {enseignant['nom']}**")
                    st.write(f"Tarif horaire: {enseignant['tarif']:.2f}€")

                with col2:
                    if st.button("✏️", key=f"edit_ens_{enseignant['id']}"):
                        st.session_state["edit_enseignant_id"] = enseignant['id']
                        st.experimental_rerun()

                with col3:
                    if st.button("🗑️", key=f"del_ens_{enseignant['id']}"):
                        if supprimer_element(data, "enseignant", enseignant['id']):
                            st.success("Enseignant supprimé avec succès!")
                            st.experimental_rerun()

                st.divider()
        else:
            st.info("Aucun enseignant enregistré")

    # Onglet Groupes
    elif onglet == "Groupes":
        st.title("Gestion des groupes")

        # Formulaire d'ajout/modification
        with st.expander("Ajouter/Modifier un groupe", expanded=True):
            edit_id = st.session_state.get("edit_groupe_id", None)
            groupe = next((g for g in data["groupes"] if g["id"] == edit_id), None) if edit_id else None

            with st.form("form_groupe"):
                nom = st.text_input("Nom du groupe*", value=groupe["nom"] if groupe else "")

                # Sélection de la promotion
                promo_options = [(p["id"], p["nom"]) for p in data["promotions"]]
                promo_id = st.selectbox(
                    "Promotion*",
                    options=promo_options,
                    format_func=lambda x: x[1],
                    index=next((i for i, (id, _) in enumerate(promo_options) if id == groupe["promo_id"]), 0) if groupe and promo_options else 0
                ) if promo_options else st.warning("Aucune promotion disponible")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Enregistrer"):
                        if not nom or not promo_options:
                            st.error("Les champs marqués d'un * sont obligatoires")
                        else:
                            if edit_id:
                                # Mise à jour
                                for g in data["groupes"]:
                                    if g["id"] == edit_id:
                                        g.update({
                                            "nom": nom,
                                            "promo_id": promo_id[0]
                                        })
                                        break
                            else:
                                # Ajout
                                data["groupes"].append({
                                    "id": max([g["id"] for g in data["groupes"]], default=0) + 1,
                                    "nom": nom,
                                    "promo_id": promo_id[0]
                                })

                            sauvegarder_donnees(data)
                            st.success("Groupe enregistré avec succès!")
                            if "edit_groupe_id" in st.session_state:
                                del st.session_state["edit_groupe_id"]
                            st.experimental_rerun()

                with col2:
                    if edit_id and st.form_submit_button("Annuler"):
                        if "edit_groupe_id" in st.session_state:
                            del st.session_state["edit_groupe_id"]
                        st.experimental_rerun()

        # Liste des groupes avec actions
        st.subheader("Liste des groupes")
        if data["groupes"]:
            for groupe in data["groupes"]:
                promo_nom = next((p["nom"] for p in data["promotions"] if p["id"] == groupe["promo_id"]), "Inconnue")

                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{groupe['nom']}**")
                    st.write(f"Promotion: {promo_nom}")

                with col2:
                    if st.button("✏️", key=f"edit_gr_{groupe['id']}"):
                        st.session_state["edit_groupe_id"] = groupe['id']
                        st.experimental_rerun()

                with col3:
                    if st.button("🗑️", key=f"del_gr_{groupe['id']}"):
                        if supprimer_element(data, "groupe", groupe['id']):
                            st.success("Groupe supprimé avec succès!")
                            st.experimental_rerun()

                st.divider()
        else:
            st.info("Aucun groupe enregistré")

    # Onglet Promotions
    elif onglet == "Promotions":
        st.title("Gestion des promotions")

        # Formulaire d'ajout/modification
        with st.expander("Ajouter/Modifier une promotion", expanded=True):
            edit_id = st.session_state.get("edit_promo_id", None)
            promo = next((p for p in data["promotions"] if p["id"] == edit_id), None) if edit_id else None

            with st.form("form_promo"):
                nom = st.text_input("Nom de la promotion*", value=promo["nom"] if promo else "")

                # Sélection de la session
                session_options = [(s["id"], s["nom"]) for s in data["sessions"]]
                session_id = st.selectbox(
                    "Session*",
                    options=session_options,
                    format_func=lambda x: x[1],
                    index=next((i for i, (id, _) in enumerate(session_options) if id == promo["session_id"]), 0) if promo and session_options else 0
                ) if session_options else st.warning("Aucune session disponible")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Enregistrer"):
                        if not nom or not session_options:
                            st.error("Les champs marqués d'un * sont obligatoires")
                        else:
                            if edit_id:
                                # Mise à jour
                                for p in data["promotions"]:
                                    if p["id"] == edit_id:
                                        p.update({
                                            "nom": nom,
                                            "session_id": session_id[0]
                                        })
                                        break
                            else:
                                # Ajout
                                data["promotions"].append({
                                    "id": max([p["id"] for p in data["promotions"]], default=0) + 1,
                                    "nom": nom,
                                    "session_id": session_id[0]
                                })

                            sauvegarder_donnees(data)
                            st.success("Promotion enregistrée avec succès!")
                            if "edit_promo_id" in st.session_state:
                                del st.session_state["edit_promo_id"]
                            st.experimental_rerun()

                with col2:
                    if edit_id and st.form_submit_button("Annuler"):
                        if "edit_promo_id" in st.session_state:
                            del st.session_state["edit_promo_id"]
                        st.experimental_rerun()

        # Liste des promotions avec actions
        st.subheader("Liste des promotions")
        if data["promotions"]:
            for promo in data["promotions"]:
                session_nom = next((s["nom"] for s in data["sessions"] if s["id"] == promo["session_id"]), "Inconnue")

                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{promo['nom']}**")
                    st.write(f"Session: {session_nom}")

                with col2:
                    if st.button("✏️", key=f"edit_pr_{promo['id']}"):
                        st.session_state["edit_promo_id"] = promo['id']
                        st.experimental_rerun()

                with col3:
                    if st.button("🗑️", key=f"del_pr_{promo['id']}"):
                        if supprimer_element(data, "promotion", promo['id']):
                            st.success("Promotion supprimée avec succès!")
                            st.experimental_rerun()

                st.divider()
        else:
            st.info("Aucune promotion enregistrée")

    # Onglet Sessions
    elif onglet == "Sessions":
        st.title("Gestion des sessions")

        # Formulaire d'ajout/modification
        with st.expander("Ajouter/Modifier une session", expanded=True):
            edit_id = st.session_state.get("edit_session_id", None)
            session = next((s for s in data["sessions"] if s["id"] == edit_id), None) if edit_id else None

            with st.form("form_session"):
                nom = st.text_input("Nom de la session*", value=session["nom"] if session else "")
                annee = st.number_input(
                    "Année*",
                    min_value=2023,
                    max_value=2030,
                    step=1,
                    value=session["annee"] if session else 2023
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Enregistrer"):
                        if not nom:
                            st.error("Le nom de la session est obligatoire")
                        else:
                            if edit_id:
                                # Mise à jour
                                for s in data["sessions"]:
                                    if s["id"] == edit_id:
                                        s.update({
                                            "nom": nom,
                                            "annee": int(annee)
                                        })
                                        break
                            else:
                                # Ajout
                                data["sessions"].append({
                                    "id": max([s["id"] for s in data["sessions"]], default=0) + 1,
                                    "nom": nom,
                                    "annee": int(annee)
                                })

                            sauvegarder_donnees(data)
                            st.success("Session enregistrée avec succès!")
                            if "edit_session_id" in st.session_state:
                                del st.session_state["edit_session_id"]
                            st.experimental_rerun()

                with col2:
                    if edit_id and st.form_submit_button("Annuler"):
                        if "edit_session_id" in st.session_state:
                            del st.session_state["edit_session_id"]
                        st.experimental_rerun()

        # Liste des sessions avec actions
        st.subheader("Liste des sessions")
        if data["sessions"]:
            for session in data["sessions"]:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{session['nom']}**")
                    st.write(f"Année: {session['annee']}")

                with col2:
                    if st.button("✏️", key=f"edit_ses_{session['id']}"):
                        st.session_state["edit_session_id"] = session['id']
                        st.experimental_rerun()

                with col3:
                    if st.button("🗑️", key=f"del_ses_{session['id']}"):
                        if supprimer_element(data, "session", session['id']):
                            st.success("Session supprimée avec succès!")
                            st.experimental_rerun()

                st.divider()
        else:
            st.info("Aucune session enregistrée")

    # Onglet Budget
    elif onglet == "Budget":
        st.title("Analyse budgétaire")

        # Budget par année civile
        afficher_budget_annuel(data["seances"])

        if data["seances"]:
            df = pd.DataFrame(data["seances"])

            # Budget par enseignant
            st.subheader("Budget par enseignant")
            budget_enseignant = df.groupby("enseignant")["cout"].sum().reset_index()
            fig1 = px.bar(
                budget_enseignant,
                x="enseignant",
                y="cout",
                title="Coût par enseignant",
                labels={"enseignant": "Enseignant", "cout": "Coût (€)"}
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Budget par promotion
            if "promotion" in df.columns:
                st.subheader("Budget par promotion")
                budget_promo = df.groupby("promotion")["cout"].sum().reset_index()
                fig2 = px.pie(
                    budget_promo,
                    values="cout",
                    names="promotion",
                    title="Répartition par promotion",
                    labels={"promotion": "Promotion", "cout": "Coût (€)"}
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Budget total
            total = df["cout"].sum()
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
            fichier = st.file_uploader("Importer un fichier JSON", type=['json'], key="import_json")
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
