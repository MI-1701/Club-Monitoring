# ============================================================
# app.py — Dashboard de monitoring physique volleyball
# ------------------------------------------------------------
# ILIAS MOUDRIKAH
#
# Systeme complet : charge (seance-RPE, ACWR, monotonie,
# contrainte), bien-etre (Hooper), sauts, croissance,
# journal des blessures et alertes individualisees (Z-scores).
#
# Lancer en local :  streamlit run app.py
# ============================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from donnees import (
    generer_donnees_demo, generer_modele_csv, valider_csv,
    generer_demo_bien_etre, generer_modele_bien_etre, valider_csv_bien_etre,
    generer_demo_anthropometrie, generer_modele_anthropometrie,
    valider_csv_anthropometrie,
    generer_demo_blessures, generer_modele_blessures, valider_csv_blessures,
    valider_saisie_tests,
    COLONNES_TESTS, LIBELLES_TESTS, SENS_AMELIORATION, ITEMS_HOOPER,
)
from calculs import (
    calculer_acwr_equipe, calculer_progression, construire_synthese_equipe,
    extraire_tests, interpreter_acwr,
    calculer_hooper, interpreter_hooper, bien_etre_du_jour,
    calculer_monotonie_contrainte, calculer_sauts_hebdo,
    calculer_croissance, calculer_disponibilite,
    construire_toutes_alertes,
)
from identites import harmoniser_donnees
from securite import preparer_pour_validation
from depot import DepotSession as DepotDonnees_session
from rapport_pdf import generer_rapport_joueuse, generer_rapport_equipe


# ------------------------------------------------------------
# CONFIGURATION GENERALE
# ------------------------------------------------------------

nom_club_session = st.session_state.get("nom_club", "CLUB")
if nom_club_session.strip() == "":
    nom_club_session = "Mon club"

st.set_page_config(
    page_title=nom_club_session + " — Monitoring",
    layout="wide",
)


# ------------------------------------------------------------
# CHARGEMENT DES DONNEES (demo ou CSV importes)
# ------------------------------------------------------------

@st.cache_data
def charger_demo():
    """Les 4 jeux de demonstration, mis en cache pour la session."""
    return {
        "seances": generer_donnees_demo(),
        "bien_etre": generer_demo_bien_etre(),
        "anthropometrie": generer_demo_anthropometrie(),
        "blessures": generer_demo_blessures(),
    }


def afficher_messages(erreurs, avertissements):
    """Affiche les retours de validation dans la barre laterale."""
    for erreur in erreurs:
        st.error(erreur)
    for avertissement in avertissements:
        st.warning(avertissement)


def obtenir_donnees():
    """Retourne (donnees, page, nom_club).
    donnees est un dictionnaire : seances (obligatoire),
    bien_etre / anthropometrie / blessures (None si absents)."""
    with st.sidebar:
        nom_club = st.text_input(
            "Nom du club / equipe",
            value="CLUB",
            key="nom_club",
            help="Ce nom apparait sur le dashboard et sur les rapports PDF.",
        )
        if nom_club.strip() == "":
            nom_club = "Mon club"

        st.title(nom_club)
        st.caption("Monitoring physique complet")

        source = st.radio(
            "Source des donnees",
            ["Donnees de demonstration", "Importer mes fichiers CSV"],
        )

        donnees = None

        if source == "Importer mes fichiers CSV":
            donnees = {"seances": None, "bien_etre": None,
                       "anthropometrie": None, "blessures": None}

            def charger_avec_securite(fichier, validateur):
                """Garde-fou securite (taille, encodage, lignes) PUIS
                validation metier. Retourne le DataFrame ou None."""
                buffer, erreur = preparer_pour_validation(fichier)
                if erreur is not None:
                    st.error(erreur)
                    return None
                df, erreurs, avertissements = validateur(buffer)
                afficher_messages(erreurs, avertissements)
                return df

            fichier_seances = st.file_uploader(
                "1. Seances (obligatoire)", type=["csv"],
                help="Une ligne par seance et par joueuse : "
                     "RPE, duree, sauts, tests. Taille max 10 Mo.",
            )
            if fichier_seances is not None:
                donnees["seances"] = charger_avec_securite(
                    fichier_seances, valider_csv
                )

            fichier_bien_etre = st.file_uploader(
                "2. Bien-etre quotidien (optionnel)", type=["csv"],
                help="Questionnaire matinal : sommeil, fatigue, "
                     "courbatures, stress (1-7).",
            )
            if fichier_bien_etre is not None:
                donnees["bien_etre"] = charger_avec_securite(
                    fichier_bien_etre, valider_csv_bien_etre
                )

            fichier_anthro = st.file_uploader(
                "3. Anthropometrie (optionnel)", type=["csv"],
                help="Mesures mensuelles : taille et masse.",
            )
            if fichier_anthro is not None:
                donnees["anthropometrie"] = charger_avec_securite(
                    fichier_anthro, valider_csv_anthropometrie
                )

            fichier_blessures = st.file_uploader(
                "4. Journal des blessures (optionnel)", type=["csv"],
                help="Un episode par ligne : type, zone, jours d'absence.",
            )
            if fichier_blessures is not None:
                donnees["blessures"] = charger_avec_securite(
                    fichier_blessures, valider_csv_blessures
                )

            if donnees["seances"] is None:
                st.info("En attente du fichier de seances — "
                        "les donnees de demonstration restent affichees.")
                donnees = None
            else:
                st.success(
                    str(len(donnees["seances"])) + " seances chargees pour "
                    + str(donnees["seances"]["nom"].nunique()) + " joueuses."
                )

        mode_demo = donnees is None
        if donnees is None:
            donnees = charger_demo()

        # Harmonisation des identites entre fichiers : les variantes
        # d'un meme nom (casse, accents, ponctuation) sont regroupees,
        # et les noms sans correspondance dans les seances sont signales.
        donnees, registre, fusions, orphelins = harmoniser_donnees(donnees)
        donnees["registre"] = registre
        for variantes, canonique in fusions:
            st.info(
                "Noms regroupes sous « " + canonique + " » : "
                + " / ".join(variantes)
            )
        for message in orphelins:
            st.warning(message)

        with st.expander("Modeles CSV a telecharger"):
            st.download_button(
                "Modele seances", data=generer_modele_csv(),
                file_name="modele_seances.csv", mime="text/csv",
            )
            st.download_button(
                "Modele bien-etre", data=generer_modele_bien_etre(),
                file_name="modele_bien_etre.csv", mime="text/csv",
            )
            st.download_button(
                "Modele anthropometrie", data=generer_modele_anthropometrie(),
                file_name="modele_anthropometrie.csv", mime="text/csv",
            )
            st.download_button(
                "Modele blessures", data=generer_modele_blessures(),
                file_name="modele_blessures.csv", mime="text/csv",
            )

        st.divider()
        page = st.radio(
            "Navigation",
            ["Vue d'equipe", "Fiche joueuse", "Saisie rapide",
             "Bien-etre", "Comparaison", "Rapports PDF", "Methode"],
        )

    return donnees, page, nom_club, mode_demo


# ------------------------------------------------------------
# GRAPHIQUES PLOTLY REUTILISABLES
# ------------------------------------------------------------

def tracer_acwr(acwr_equipe, nom):
    """Courbe ACWR interactive avec zones colorees."""
    donnees = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])

    figure = go.Figure()
    figure.add_hrect(y0=0.0, y1=0.8, fillcolor="#4A90D9", opacity=0.10, line_width=0)
    figure.add_hrect(y0=0.8, y1=1.3, fillcolor="#2E9E5B", opacity=0.12, line_width=0)
    figure.add_hrect(y0=1.3, y1=1.5, fillcolor="#E8A13C", opacity=0.12, line_width=0)
    figure.add_hrect(y0=1.5, y1=2.2, fillcolor="#D64545", opacity=0.10, line_width=0)

    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["acwr"],
            mode="lines", name="ACWR",
            line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>ACWR : %{y:.2f}<extra></extra>",
        ))

    figure.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[0, 2.2], title="ACWR"),
        title="Ratio charge aigue / chronique",
        showlegend=False,
    )
    return figure


def tracer_evolution_test(df, noms, colonne):
    """Courbes d'evolution d'un test pour une ou plusieurs joueuses."""
    figure = go.Figure()

    couleurs = ["#12303F", "#1B6B93", "#5FA8D3", "#D64545",
                "#2E9E5B", "#8E44AD", "#E8A13C", "#C77B3F"]

    position = 0
    for nom in noms:
        tests = extraire_tests(df, nom)
        valeurs = tests.dropna(subset=[colonne])
        if len(valeurs) > 0:
            figure.add_trace(go.Scatter(
                x=valeurs["date"], y=valeurs[colonne],
                mode="lines+markers", name=nom,
                line=dict(color=couleurs[position % len(couleurs)], width=2),
                hovertemplate="%{x|%d/%m/%Y}<br>%{y}<extra>" + nom + "</extra>",
            ))
        position = position + 1

    figure.update_layout(
        height=360, margin=dict(l=10, r=10, t=30, b=10),
        title=LIBELLES_TESTS[colonne],
    )
    return figure


def tracer_hooper(df_bien_etre, nom):
    """Courbe de l'indice de Hooper avec zones indicatives."""
    df = calculer_hooper(df_bien_etre)
    donnees = df[df["nom"] == nom].sort_values("date")

    figure = go.Figure()
    figure.add_hrect(y0=4, y1=13, fillcolor="#2E9E5B", opacity=0.10, line_width=0)
    figure.add_hrect(y0=13, y1=19, fillcolor="#E8A13C", opacity=0.10, line_width=0)
    figure.add_hrect(y0=19, y1=28, fillcolor="#D64545", opacity=0.10, line_width=0)

    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["hooper"],
            mode="lines", line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>Hooper : %{y}<extra></extra>",
        ))

    figure.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[4, 28], title="Indice de Hooper"),
        title="Bien-etre quotidien (plus bas = mieux)",
        showlegend=False,
    )
    return figure


def tracer_monotonie_contrainte(monotonie, nom):
    """Deux courbes : monotonie et contrainte (axes separes)."""
    donnees = monotonie[monotonie["nom"] == nom].dropna(subset=["monotonie"])

    figure = go.Figure()
    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["monotonie"],
            mode="lines", name="Monotonie",
            line=dict(color="#1B6B93", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>Monotonie : %{y:.2f}<extra></extra>",
        ))
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["contrainte"],
            mode="lines", name="Contrainte", yaxis="y2",
            line=dict(color="#C77B3F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>Contrainte : %{y:.0f}<extra></extra>",
        ))
        figure.add_hline(y=2.0, line_dash="dot", line_color="#D64545",
                         annotation_text="Monotonie 2.0")

    figure.update_layout(
        height=320, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Monotonie"),
        yaxis2=dict(title="Contrainte (UA)", overlaying="y", side="right"),
        title="Monotonie et contrainte (Foster)",
        legend=dict(orientation="h", y=1.15),
    )
    return figure


def tracer_sauts(sauts_hebdo, nom):
    """Barres du volume hebdomadaire de sauts."""
    donnees = sauts_hebdo[sauts_hebdo["nom"] == nom]

    figure = go.Figure()
    if len(donnees) > 0:
        figure.add_trace(go.Bar(
            x=donnees["semaine"], y=donnees["sauts"],
            marker_color="#1B6B93", marker_line_color="#12303F",
            marker_line_width=1,
            hovertemplate="Semaine du %{x|%d/%m}<br>%{y} sauts<extra></extra>",
        ))

    figure.update_layout(
        height=280, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Sauts / semaine"),
        title="Volume de sauts hebdomadaire",
    )
    return figure


def tracer_croissance(croissance, nom):
    """Courbe de taille avec vitesse estimee en infobulle."""
    donnees = croissance[croissance["nom"] == nom].sort_values("date")

    figure = go.Figure()
    if len(donnees) > 0:
        textes = []
        for indice in range(len(donnees)):
            vitesse = donnees["vitesse_cm_an"].iloc[indice]
            if pd.isna(vitesse):
                textes.append("Premiere mesure")
            else:
                textes.append("Vitesse : " + str(round(float(vitesse), 1)) + " cm/an")

        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["taille_cm"],
            mode="lines+markers", text=textes,
            line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>Taille : %{y} cm<br>%{text}<extra></extra>",
        ))

    figure.update_layout(
        height=280, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Taille (cm)"),
        title="Croissance",
        showlegend=False,
    )
    return figure


# ------------------------------------------------------------
# AFFICHAGE DU CENTRE D'ALERTES
# ------------------------------------------------------------

def afficher_centre_alertes(donnees):
    """Affiche les alertes construites par calculs.construire_toutes_alertes
    (fusion ACWR + individualisees, deja triees par gravite)."""
    toutes_alertes = construire_toutes_alertes(
        donnees["seances"], donnees["bien_etre"], donnees["anthropometrie"]
    )

    if len(toutes_alertes) == 0:
        st.success("Aucune alerte : tous les indicateurs sont dans les normes.")
        return

    st.subheader("Centre d'alertes (" + str(len(toutes_alertes)) + ")")
    for alerte in toutes_alertes:
        texte = ("**" + alerte["nom"] + "** · " + alerte["module"]
                 + " — " + alerte["message"])
        if alerte["niveau"] == "alerte":
            st.error(texte)
        else:
            st.warning(texte)


# ------------------------------------------------------------
# PAGE 1 — VUE D'EQUIPE
# ------------------------------------------------------------

def page_vue_equipe(donnees):
    st.header("Vue d'equipe")

    df = donnees["seances"]
    synthese, acwr_equipe = construire_synthese_equipe(df)

    colonne_a, colonne_b, colonne_c, colonne_d = st.columns(4)

    nb_joueuses = df["nom"].nunique()
    nb_seances = len(df.dropna(subset=["rpe", "duree_min"]))
    cmj_moyen = synthese["CMJ (cm)"].mean()

    colonne_a.metric("Joueuses suivies", nb_joueuses)
    colonne_b.metric("Seances enregistrees", nb_seances)

    if donnees["bien_etre"] is not None:
        matrice = bien_etre_du_jour(donnees["bien_etre"])
        hooper_moyen = matrice["Hooper"].mean()
        colonne_c.metric("Hooper moyen (dernier jour)", round(hooper_moyen, 1))
    else:
        colonne_c.metric("Hooper moyen", "—")

    if pd.notna(cmj_moyen):
        colonne_d.metric("CMJ moyen equipe", str(round(cmj_moyen, 1)) + " cm")
    else:
        colonne_d.metric("CMJ moyen equipe", "—")

    afficher_centre_alertes(donnees)

    # --- Tableau de synthese --------------------------------
    st.subheader("Synthese par joueuse")

    tableau = synthese.copy()

    # Ajouter le bien-etre du jour si disponible
    if donnees["bien_etre"] is not None:
        matrice = bien_etre_du_jour(donnees["bien_etre"])
        hooper_par_joueuse = {}
        for indice in range(len(matrice)):
            hooper_par_joueuse[matrice["Joueuse"].iloc[indice]] = matrice["Etat"].iloc[indice]
        valeurs_bien_etre = []
        for indice in range(len(tableau)):
            nom = tableau["Joueuse"].iloc[indice]
            valeurs_bien_etre.append(hooper_par_joueuse.get(nom, "—"))
        tableau["Bien-etre"] = valeurs_bien_etre

    tableau["CMJ (cm)"] = tableau["CMJ (cm)"].round(1)
    tableau["Attaque (cm)"] = tableau["Attaque (cm)"].round(0)
    tableau["Sprint 10 m (s)"] = tableau["Sprint 10 m (s)"].round(2)
    tableau["ACWR"] = tableau["ACWR"].round(2)
    st.dataframe(tableau, use_container_width=True, hide_index=True)

    # --- Disponibilite --------------------------------------
    if donnees["blessures"] is not None:
        st.subheader("Disponibilite")
        disponibilite = calculer_disponibilite(donnees["blessures"], df)
        st.dataframe(disponibilite, use_container_width=True, hide_index=True)
        st.caption(
            "Jours d'absence recadres sur la periode des seances ; "
            "les episodes qui se chevauchent ne sont comptes qu'une fois."
        )

    # --- Charge collective ----------------------------------
    st.subheader("Charge hebdomadaire de l'equipe")

    donnees_charge = df.dropna(subset=["rpe", "duree_min"]).copy()
    donnees_charge["charge"] = donnees_charge["rpe"] * donnees_charge["duree_min"]
    donnees_charge["semaine"] = donnees_charge["date"].dt.to_period("W").dt.start_time
    charge_hebdo = donnees_charge.groupby("semaine", as_index=False)["charge"].sum()

    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=charge_hebdo["semaine"], y=charge_hebdo["charge"],
        marker_color="#1B6B93", marker_line_color="#12303F",
        marker_line_width=1,
        hovertemplate="Semaine du %{x|%d/%m}<br>Charge totale : %{y:.0f} UA<extra></extra>",
    ))
    figure.update_layout(
        height=300, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(title="Charge (unites arbitraires)"),
    )
    st.plotly_chart(figure, use_container_width=True)


# ------------------------------------------------------------
# PAGE 2 — BIEN-ETRE DU JOUR
# ------------------------------------------------------------

def page_bien_etre(donnees):
    st.header("Bien-etre de l'equipe")

    if donnees["bien_etre"] is None:
        st.info(
            "Aucune donnee de bien-etre importee. Telechargez le modele "
            "dans la barre laterale : chaque joueuse note chaque matin "
            "son sommeil, sa fatigue, ses courbatures et son stress "
            "de 1 (tres bien) a 7 (tres mauvais)."
        )
        return

    matrice = bien_etre_du_jour(donnees["bien_etre"])

    st.subheader("Matrice du jour")
    st.caption("Dernieres reponses de chaque joueuse. "
               "Echelle 1 (tres bien) a 7 (tres mauvais).")
    st.dataframe(matrice, use_container_width=True, hide_index=True)

    st.subheader("Evolution individuelle")
    noms_disponibles = sorted(donnees["bien_etre"]["nom"].unique())
    nom = st.selectbox("Joueuse", noms_disponibles)
    st.plotly_chart(tracer_hooper(donnees["bien_etre"], nom),
                    use_container_width=True)

    # Detail des 4 composantes sur les 14 derniers jours
    st.subheader("Detail des 14 derniers jours")
    df = donnees["bien_etre"]
    donnees_joueuse = df[df["nom"] == nom].sort_values("date").tail(14)
    if len(donnees_joueuse) > 0:
        figure = go.Figure()
        couleurs_items = {
            "sommeil": "#1B6B93", "fatigue": "#C77B3F",
            "courbatures": "#8E44AD", "stress": "#D64545",
        }
        for item in ITEMS_HOOPER:
            figure.add_trace(go.Scatter(
                x=donnees_joueuse["date"], y=donnees_joueuse[item],
                mode="lines+markers", name=item.capitalize(),
                line=dict(color=couleurs_items[item], width=2),
            ))
        figure.update_layout(
            height=320, margin=dict(l=10, r=10, t=50, b=10),
            yaxis=dict(range=[0.5, 7.5], title="Score (1-7)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        st.plotly_chart(figure, use_container_width=True)


# ------------------------------------------------------------
# PAGE 3 — FICHE JOUEUSE
# ------------------------------------------------------------

def page_fiche_joueuse(donnees):
    st.header("Fiche joueuse")

    df = donnees["seances"]
    noms_disponibles = sorted(df["nom"].unique())
    nom = st.selectbox("Choisir une joueuse", noms_disponibles)

    donnees_joueuse = df[df["nom"] == nom]
    poste = donnees_joueuse["poste"].iloc[-1]
    st.caption("Poste : " + poste)

    # --- Synthese instantanee (vue 360) ---------------------
    # Etat du jour de la joueuse avant tout detail : charge,
    # bien-etre, disponibilite et alertes actives.
    acwr_equipe = calculer_acwr_equipe(df)
    toutes_alertes = construire_toutes_alertes(
        df, donnees["bien_etre"], donnees["anthropometrie"]
    )
    alertes_joueuse = []
    for alerte in toutes_alertes:
        if alerte["nom"] == nom:
            alertes_joueuse.append(alerte)

    colonne_a, colonne_b, colonne_c, colonne_d = st.columns(4)

    donnees_acwr = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])
    if len(donnees_acwr) > 0:
        acwr_actuel = float(donnees_acwr["acwr"].iloc[-1])
        etiquette_acwr, couleur_acwr, emoji_acwr = interpreter_acwr(acwr_actuel)
        colonne_a.metric("ACWR", emoji_acwr + " " + str(round(acwr_actuel, 2)),
                         help=etiquette_acwr)
    else:
        colonne_a.metric("ACWR", "—", help="Historique insuffisant (28 jours)")

    if donnees["bien_etre"] is not None:
        df_hooper = calculer_hooper(donnees["bien_etre"])
        reponses = df_hooper[df_hooper["nom"] == nom].sort_values("date")
        if len(reponses) > 0:
            hooper_jour = int(reponses["hooper"].iloc[-1])
            etiquette_h, emoji_h = interpreter_hooper(float(hooper_jour))
            colonne_b.metric("Bien-etre (Hooper)",
                             emoji_h + " " + str(hooper_jour),
                             help=etiquette_h + " — echelle 4 (excellent) a 28")
        else:
            colonne_b.metric("Bien-etre (Hooper)", "—")
    else:
        colonne_b.metric("Bien-etre (Hooper)", "—")

    if donnees["blessures"] is not None:
        disponibilite = calculer_disponibilite(donnees["blessures"], df)
        ligne_dispo = disponibilite[disponibilite["Joueuse"] == nom]
        if len(ligne_dispo) > 0:
            colonne_c.metric(
                "Disponibilite",
                str(ligne_dispo["Disponibilite (%)"].iloc[0]) + " %",
                help=str(ligne_dispo["Episodes"].iloc[0]) + " episode(s), "
                     + str(ligne_dispo["Jours d'absence"].iloc[0])
                     + " jour(s) d'absence",
            )
        else:
            colonne_c.metric("Disponibilite", "—")
    else:
        colonne_c.metric("Disponibilite", "—")

    colonne_d.metric("Alertes actives", str(len(alertes_joueuse)))

    if len(alertes_joueuse) > 0:
        for alerte in alertes_joueuse:
            texte = alerte["module"] + " — " + alerte["message"]
            if alerte["niveau"] == "alerte":
                st.error(texte)
            else:
                st.warning(texte)
    else:
        st.caption("Aucune alerte active pour cette joueuse.")

    # --- Progression sur les tests --------------------------
    progression = calculer_progression(df, nom)

    if len(progression) == 0:
        st.info("Pas encore assez de tests pour mesurer une progression "
                "(2 releves minimum par indicateur).")
    else:
        # Liste ordonnee des tests disponibles pour cette joueuse
        tests_presents = []
        for colonne_test in COLONNES_TESTS:
            if colonne_test in progression:
                tests_presents.append(colonne_test)

        # Affichage par rangees de 4 metriques maximum
        for debut in range(0, len(tests_presents), 4):
            groupe = tests_presents[debut:debut + 4]
            colonnes_metriques = st.columns(4)
            position = 0
            for colonne_test in groupe:
                info = progression[colonne_test]

                signe = ""
                if info["delta"] > 0:
                    signe = "+"

                if SENS_AMELIORATION[colonne_test]:
                    sens_couleur = "normal"
                else:
                    sens_couleur = "inverse"

                colonnes_metriques[position].metric(
                    LIBELLES_TESTS[colonne_test],
                    round(info["dernier"], 2),
                    delta=signe + str(round(info["delta"], 2)),
                    delta_color=sens_couleur,
                )
                position = position + 1

    # --- Onglets thematiques --------------------------------
    onglet_tests, onglet_charge, onglet_bien_etre, onglet_corps, onglet_blessures = st.tabs(
        ["Tests", "Charge", "Bien-etre", "Croissance", "Blessures"]
    )

    with onglet_tests:
        choix_test = st.selectbox(
            "Indicateur", COLONNES_TESTS,
            format_func=LIBELLES_TESTS.get,
        )
        st.plotly_chart(
            tracer_evolution_test(df, [nom], choix_test),
            use_container_width=True,
        )

    with onglet_charge:
        donnees_acwr = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])

        if len(donnees_acwr) == 0:
            st.info("Historique insuffisant pour l'ACWR "
                    "(28 jours de seances minimum).")
        else:
            acwr_actuel = float(donnees_acwr["acwr"].iloc[-1])
            etiquette, couleur, emoji = interpreter_acwr(acwr_actuel)
            st.markdown(emoji + " ACWR actuel : **"
                        + str(round(acwr_actuel, 2)) + "** — " + etiquette)
            st.plotly_chart(tracer_acwr(acwr_equipe, nom),
                            use_container_width=True)

        monotonie = calculer_monotonie_contrainte(df)
        st.plotly_chart(tracer_monotonie_contrainte(monotonie, nom),
                        use_container_width=True)

        sauts_hebdo = calculer_sauts_hebdo(df)
        if len(sauts_hebdo[sauts_hebdo["nom"] == nom]) > 0:
            st.plotly_chart(tracer_sauts(sauts_hebdo, nom),
                            use_container_width=True)
        else:
            st.info("Pas de donnees de sauts pour cette joueuse "
                    "(colonne « sauts » du fichier seances).")

    with onglet_bien_etre:
        if donnees["bien_etre"] is None:
            st.info("Aucune donnee de bien-etre importee.")
        else:
            df_be = donnees["bien_etre"]
            if len(df_be[df_be["nom"] == nom]) == 0:
                st.info("Pas de reponses pour cette joueuse.")
            else:
                st.plotly_chart(tracer_hooper(df_be, nom),
                                use_container_width=True)

    with onglet_corps:
        if donnees["anthropometrie"] is None:
            st.info("Aucune donnee anthropometrique importee.")
        else:
            croissance = calculer_croissance(donnees["anthropometrie"])
            donnees_croissance = croissance[croissance["nom"] == nom]
            if len(donnees_croissance) == 0:
                st.info("Pas de mesures pour cette joueuse.")
            else:
                derniere_vitesse = donnees_croissance["vitesse_cm_an"].dropna()
                if len(derniere_vitesse) > 0:
                    vitesse = float(derniere_vitesse.iloc[-1])
                    if vitesse > 7.0:
                        st.warning(
                            "Vitesse de croissance estimee : "
                            + str(round(vitesse, 1))
                            + " cm/an — pic de croissance probable. "
                            + "Periode de vigilance : moduler charge et sauts."
                        )
                    else:
                        st.markdown("Vitesse de croissance estimee : **"
                                    + str(round(vitesse, 1)) + " cm/an**")
                st.plotly_chart(tracer_croissance(croissance, nom),
                                use_container_width=True)

    with onglet_blessures:
        if donnees["blessures"] is None:
            st.info("Aucun journal de blessures importe.")
        else:
            episodes = donnees["blessures"][donnees["blessures"]["nom"] == nom]
            if len(episodes) == 0:
                st.success("Aucun episode enregistre pour cette joueuse.")
            else:
                affichage = episodes.copy()
                affichage["date_debut"] = affichage["date_debut"].dt.strftime("%d/%m/%Y")
                affichage = affichage.rename(columns={
                    "date_debut": "Debut", "type": "Type",
                    "zone": "Zone", "jours_absence": "Jours d'absence",
                })
                st.dataframe(
                    affichage[["Debut", "Type", "Zone", "Jours d'absence"]],
                    use_container_width=True, hide_index=True,
                )


# ------------------------------------------------------------
# PAGE 4 — COMPARAISON
# ------------------------------------------------------------

def page_comparaison(donnees):
    st.header("Comparaison entre joueuses")

    df = donnees["seances"]
    noms_disponibles = sorted(df["nom"].unique())
    noms_choisis = st.multiselect(
        "Joueuses a comparer", noms_disponibles,
        default=noms_disponibles[:3],
    )

    if len(noms_choisis) < 2:
        st.info("Selectionnez au moins deux joueuses.")
        return

    choix_test = st.selectbox(
        "Indicateur", COLONNES_TESTS,
        format_func=LIBELLES_TESTS.get,
    )

    st.plotly_chart(
        tracer_evolution_test(df, noms_choisis, choix_test),
        use_container_width=True,
    )

    st.subheader("Dernier releve par joueuse")

    lignes = []
    for nom in noms_choisis:
        tests = extraire_tests(df, nom)
        valeurs = tests.dropna(subset=[choix_test])
        if len(valeurs) > 0:
            lignes.append({
                "Joueuse": nom,
                "Date": valeurs["date"].iloc[-1].strftime("%d/%m/%Y"),
                "Valeur": float(valeurs[choix_test].iloc[-1]),
            })

    if len(lignes) > 0:
        classement = pd.DataFrame(lignes)
        meilleur_en_haut = SENS_AMELIORATION[choix_test]
        classement = classement.sort_values(
            "Valeur", ascending=not meilleur_en_haut
        ).reset_index(drop=True)
        st.dataframe(classement, use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# PAGE 5 — RAPPORTS PDF
# ------------------------------------------------------------

def page_rapports(donnees, nom_club):
    st.header("Rapports PDF")
    st.write(
        "Generez un rapport pret a partager avec le staff, "
        "les parents ou la direction du club."
    )

    df = donnees["seances"]
    nom_fichier_club = nom_club.lower().strip().replace(" ", "_")

    colonne_gauche, colonne_droite = st.columns(2)

    with colonne_gauche:
        st.subheader("Fiche individuelle")
        noms_disponibles = sorted(df["nom"].unique())
        nom = st.selectbox("Joueuse", noms_disponibles)

        if st.button("Generer la fiche", type="primary"):
            with st.spinner("Creation du PDF en cours..."):
                st.session_state["pdf_joueuse"] = generer_rapport_joueuse(
                    df, nom, nom_club, donnees["bien_etre"]
                )
                st.session_state["pdf_joueuse_nom"] = nom

        # Le bouton de telechargement persiste apres le rerun Streamlit
        # (sinon il disparait des le premier clic)
        if (st.session_state.get("pdf_joueuse") is not None
                and st.session_state.get("pdf_joueuse_nom") == nom):
            st.download_button(
                "📄 Telecharger la fiche de " + nom,
                data=st.session_state["pdf_joueuse"],
                file_name="fiche_" + nom.replace(" ", "_") + ".pdf",
                mime="application/pdf",
            )

    with colonne_droite:
        st.subheader("Synthese d'equipe")
        st.write("Tableau complet + alertes de charge, sur une page.")

        if st.button("Generer la synthese", type="primary"):
            with st.spinner("Creation du PDF en cours..."):
                st.session_state["pdf_equipe"] = generer_rapport_equipe(
                    df, nom_club
                )

        if st.session_state.get("pdf_equipe") is not None:
            st.download_button(
                "📄 Telecharger la synthese d'equipe",
                data=st.session_state["pdf_equipe"],
                file_name="synthese_equipe_" + nom_fichier_club + ".pdf",
                mime="application/pdf",
            )


# ------------------------------------------------------------
# PAGE 6 — METHODE
# ------------------------------------------------------------

def page_methode():
    st.header("Methode et references")

    st.markdown(
        """
**1. Charge d'entrainement — methode seance-RPE (Foster, 2001)**

Chaque seance recoit une charge : `RPE (1-10) x duree en minutes`.
Aucun capteur necessaire, seulement la perception d'effort.

**2. ACWR — Acute:Chronic Workload Ratio**

Charge des 7 derniers jours divisee par la moyenne hebdomadaire des
28 derniers jours (moyennes glissantes couplees). La zone **0,80 - 1,30**
est un repere descriptif issu de la litterature initiale (Gabbett, 2016),
mais la valeur predictive individuelle de l'ACWR est aujourd'hui
contestee (Impellizzeri et al., 2020). Ici, l'ACWR est donc lu comme un
**signal de variation inhabituelle de charge** qui oriente l'attention
de l'entraineur — pas comme une prediction de blessure.

**3. Monotonie et contrainte (Foster)**

- Monotonie = moyenne des charges quotidiennes / ecart-type (7 jours).
  Au-dela de **2,0** : entrainement trop uniforme, meme a charge moderee.
- Contrainte = charge hebdomadaire x monotonie. Evaluee par rapport
  a l'historique personnel de chaque joueuse (Z-score).

**4. Bien-etre — questionnaire de Hooper (Hooper & Mackinnon, 1995)**

Chaque matin : sommeil, fatigue, courbatures et stress notes de
1 (tres bien) a 7 (tres mauvais). Indice = somme (4 a 28).
Les seuils affiches (13 / 19) sont indicatifs : la reference
principale est l'ecart de chaque joueuse a sa propre norme.

**5. Charge de sauts**

Volume de sauts hebdomadaire, l'indicateur specifique du volleyball
(prevention des tendinopathies rotuliennes). Une hausse de plus de
50 % par rapport a la moyenne personnelle des 4 semaines declenche
une vigilance.

**6. Croissance**

Vitesse estimee entre mesures espacees d'au moins 60 jours. Au-dela
d'environ **7 cm/an** : pic de croissance probable, periode de
vulnerabilite accrue (Lloyd & Oliver, 2012) — moduler charge et sauts.

**7. Alertes individualisees (Z-scores)**

Chaque joueuse est comparee a **sa propre reference** plutot qu'a des
seuils universels : `Z = (valeur - moyenne personnelle) / ecart-type`.
Un Z superieur a +1,5 declenche une vigilance, superieur a +2,5 une alerte.

---

**Limites.** Ces indicateurs orientent l'attention de l'entraineur ;
ils ne remplacent ni le jugement du staff ni l'avis medical. Les seuils
sont issus d'etudes sur des populations variees et doivent etre
interpretes avec prudence chez les jeunes athletes.

**References.** Foster et al. (2001) · Hooper & Mackinnon (1995) ·
Gabbett (2016) · Impellizzeri et al. (2019, 2020 — critique de l'ACWR) ·
Lloyd & Oliver (2012) · Bahr & Visnes (tendinopathie rotulienne et
charge de sauts).
        """
    )


# ------------------------------------------------------------
# POINT D'ENTREE
# ------------------------------------------------------------

# ------------------------------------------------------------
# PAGE — SAISIE RAPIDE DE TESTS (Sprint 2)
# ------------------------------------------------------------

def page_saisie_rapide(depot, mode_demo, nom_club):
    st.header("Saisie rapide d'un test")
    st.write(
        "Enregistrez un test pour toute l'equipe en une fois. "
        "La validation est atomique : tant qu'une valeur est "
        "invalide, rien n'est enregistre."
    )

    noms = depot.noms_joueuses()
    if len(noms) == 0:
        st.info("Aucune joueuse disponible. Chargez d'abord des seances.")
        return

    postes = depot.postes_par_joueuse()

    colonne_gauche, colonne_droite = st.columns(2)
    with colonne_gauche:
        libelle_choisi = st.selectbox(
            "Test a saisir",
            [LIBELLES_TESTS[c] for c in COLONNES_TESTS],
        )
        colonne_test = None
        for cle in COLONNES_TESTS:
            if LIBELLES_TESTS[cle] == libelle_choisi:
                colonne_test = cle
                break
    with colonne_droite:
        date_test = st.date_input("Date du test", value=pd.Timestamp.today())

    st.caption(
        "Laissez une cellule vide pour une joueuse non testee ce jour."
    )

    # Grille pre-remplie avec l'effectif ; l'entraineur ne saisit
    # que la colonne « Resultat ».
    grille = pd.DataFrame({
        "Joueuse": noms,
        "Poste": [postes.get(nom, "") for nom in noms],
        "Resultat": [None] * len(noms),
    })

    edite = st.data_editor(
        grille,
        use_container_width=True, hide_index=True,
        disabled=["Joueuse", "Poste"],
        column_config={
            "Resultat": st.column_config.NumberColumn(
                "Resultat (" + libelle_choisi + ")",
                help="Valeur mesuree ; vide si non teste.",
                format="%.2f",
            )
        },
        key="grille_saisie",
    )

    # Construire le lot et valider (atomique)
    lignes = []
    for indice in range(len(edite)):
        lignes.append({
            "nom": edite["Joueuse"].iloc[indice],
            "poste": edite["Poste"].iloc[indice],
            "valeur": edite["Resultat"].iloc[indice],
        })

    valides, erreurs = valider_saisie_tests(lignes, colonne_test)
    nb_saisis = sum(
        1 for ligne in lignes
        if ligne["valeur"] is not None and str(ligne["valeur"]).strip() != ""
    )

    st.divider()

    if erreurs:
        st.error(
            "⚠ " + str(len(valides)) + "/" + str(nb_saisis)
            + " valeur(s) valide(s) — corrigez avant d'enregistrer :"
        )
        for message in erreurs:
            st.write("• " + message)
        return

    if nb_saisis == 0:
        st.info("Saisissez au moins un resultat pour continuer.")
        return

    st.success(
        "✓ " + str(len(valides)) + "/" + str(nb_saisis)
        + " valeur(s) valide(s). Apercu avant enregistrement :"
    )

    apercu = pd.DataFrame([{
        "Joueuse": v["nom"],
        "Date": pd.Timestamp(date_test).strftime("%d/%m/%Y"),
        libelle_choisi: v[colonne_test],
    } for v in valides])
    st.dataframe(apercu, use_container_width=True, hide_index=True)

    if st.button("Enregistrer ces resultats", type="primary"):
        lignes_a_ajouter = []
        for v in valides:
            ligne = {
                "date": pd.Timestamp(date_test),
                "nom": v["nom"],
                "poste": v["poste"],
                colonne_test: v[colonne_test],
            }
            lignes_a_ajouter.append(ligne)
        nb = depot.ajouter_mesures_tests(lignes_a_ajouter)
        st.session_state["saisie_confirmee"] = nb
        st.session_state["export_pret"] = depot.exporter_seances_csv()

    if st.session_state.get("saisie_confirmee"):
        nb = st.session_state["saisie_confirmee"]
        st.success(
            str(nb) + " resultat(s) ajoute(s) a la session. "
            "Ils apparaissent immediatement dans les fiches et alertes."
        )
        if mode_demo:
            st.warning(
                "Mode demonstration : ces valeurs restent en memoire "
                "de session. Telechargez le CSV mis a jour pour les "
                "conserver et le recharger ensuite en mode import."
            )
        nom_fichier = nom_club.lower().strip().replace(" ", "_")
        st.download_button(
            "📥 Telecharger le CSV seances mis a jour",
            data=st.session_state.get("export_pret", b""),
            file_name="seances_" + nom_fichier + ".csv",
            mime="text/csv",
        )
        st.caption(
            "Rechargez ce fichier via « Importer mes fichiers CSV » "
            "a la prochaine session pour retrouver ces resultats."
        )


def principal():
    donnees, page, nom_club, mode_demo = obtenir_donnees()
    depot = DepotDonnees_session(donnees)

    if mode_demo:
        st.info(
            "🟦 **Donnees de demonstration** — joueuses fictives. "
            "Passez a « Importer mes fichiers CSV » dans la barre "
            "laterale pour analyser vos propres donnees."
        )

    if page == "Vue d'equipe":
        page_vue_equipe(donnees)
    elif page == "Fiche joueuse":
        page_fiche_joueuse(donnees)
    elif page == "Saisie rapide":
        page_saisie_rapide(depot, mode_demo, nom_club)
    elif page == "Bien-etre":
        page_bien_etre(donnees)
    elif page == "Comparaison":
        page_comparaison(donnees)
    elif page == "Rapports PDF":
        page_rapports(donnees, nom_club)
    else:
        page_methode()

    st.sidebar.divider()
    with st.sidebar.expander("Confidentialite & securite"):
        st.markdown(
            "Les donnees importees sont **traitees en memoire pendant "
            "la session** ; l'application ne les persiste dans aucune "
            "base de donnees. Import limite a 10 Mo, fichiers valides "
            "avant analyse. L'hebergement (Streamlit Community Cloud) "
            "fournit le HTTPS.\n\n"
            "Ne pas deposer de donnees reelles d'athletes mineures sur "
            "la demonstration publique."
        )
    st.sidebar.caption(
        "Concu par Ilias Moudrikah · seance-RPE · ACWR · Hooper · Z-scores"
    )


principal()
