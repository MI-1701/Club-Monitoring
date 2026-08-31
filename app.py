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
    extraire_tests, interpreter_acwr, cle_acwr,
    calculer_hooper, interpreter_hooper, bien_etre_du_jour,
    calculer_monotonie_contrainte, calculer_sauts_hebdo,
    calculer_croissance, calculer_disponibilite,
    construire_toutes_alertes,
)
from identites import harmoniser_donnees
from securite import preparer_pour_validation
from depot import DepotSession as DepotDonnees_session
from i18n import (
    t, traduire_alerte, etiquette_acwr, langue_courante,
    LANGUES, LANGUE_DEFAUT,
)
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

    # Detection du parametre URL ?demo=true pour auto-load
    params = st.query_params
    auto_demo = params.get("demo", "false").lower() == "true"

    with st.sidebar:
        # Selecteur de langue — en tete, pour que toute la session
        # s'affiche dans la langue choisie.
        codes = list(LANGUES.keys())
        st.selectbox(
            t("langue_label"),
            codes,
            index=codes.index(st.session_state.get("langue", LANGUE_DEFAUT)),
            format_func=lambda c: LANGUES[c],
            key="langue",
        )

        nom_club = st.text_input(
            t("nom_club_label"),
            value="CLUB",
            key="nom_club",
            help=t("nom_club_help"),
        )
        if nom_club.strip() == "":
            nom_club = "Mon club"

        st.title(nom_club)
        st.caption(t("monitoring_complet"))

        source = st.radio(
            t("source_donnees"),
            ["Donnees de demonstration", "Importer mes fichiers CSV"],
            format_func=lambda v: (
                t("source_demo") if v == "Donnees de demonstration"
                else t("source_import")
            ),
            index=0 if auto_demo else None,
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
                t("up_seances"), type=["csv"],
                help=t("up_seances_help"),
            )
            if fichier_seances is not None:
                donnees["seances"] = charger_avec_securite(
                    fichier_seances, valider_csv
                )

            fichier_bien_etre = st.file_uploader(
                t("up_bien_etre"), type=["csv"],
                help=t("up_bien_etre_help"),
            )
            if fichier_bien_etre is not None:
                donnees["bien_etre"] = charger_avec_securite(
                    fichier_bien_etre, valider_csv_bien_etre
                )

            fichier_anthro = st.file_uploader(
                t("up_anthro"), type=["csv"],
                help=t("up_anthro_help"),
            )
            if fichier_anthro is not None:
                donnees["anthropometrie"] = charger_avec_securite(
                    fichier_anthro, valider_csv_anthropometrie
                )

            fichier_blessures = st.file_uploader(
                t("up_blessures"), type=["csv"],
                help=t("up_blessures_help"),
            )
            if fichier_blessures is not None:
                donnees["blessures"] = charger_avec_securite(
                    fichier_blessures, valider_csv_blessures
                )

            if donnees["seances"] is None:
                st.info(t("attente_seances"))
                donnees = None
            else:
                st.success(t(
                    "seances_chargees",
                    n=len(donnees["seances"]),
                    j=donnees["seances"]["nom"].nunique(),
                ))

        mode_demo = donnees is None
        if donnees is None:
            donnees = charger_demo()
            if auto_demo:
                st.success(t("demo_auto_chargee"))

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

        with st.expander(t("modeles_expander")):
            st.download_button(
                t("modele_seances"), data=generer_modele_csv(),
                file_name="modele_seances.csv", mime="text/csv",
            )
            st.download_button(
                t("modele_bien_etre"), data=generer_modele_bien_etre(),
                file_name="modele_bien_etre.csv", mime="text/csv",
            )
            st.download_button(
                t("modele_anthro"), data=generer_modele_anthropometrie(),
                file_name="modele_anthropometrie.csv", mime="text/csv",
            )
            st.download_button(
                t("modele_blessures"), data=generer_modele_blessures(),
                file_name="modele_blessures.csv", mime="text/csv",
            )

        st.divider()
        # Les valeurs internes restent stables (routage) ; seul
        # l'affichage est traduit via format_func.
        pages_cles = ["Vue d'equipe", "Fiche joueuse", "Saisie rapide",
                      "Bien-etre", "Comparaison", "Rapports PDF", "Methode"]
        libelles_pages = {
            "Vue d'equipe": t("page_equipe"),
            "Fiche joueuse": t("page_fiche"),
            "Saisie rapide": t("page_saisie"),
            "Bien-etre": t("page_bien_etre"),
            "Comparaison": t("page_comparaison"),
            "Rapports PDF": t("page_rapports"),
            "Methode": t("page_methode"),
        }
        page = st.radio(
            t("navigation"),
            pages_cles,
            format_func=lambda c: libelles_pages[c],
        )

    return donnees, page, nom_club, mode_demo


# ------------------------------------------------------------
# GRAPHIQUES PLOTLY REUTILISABLES
# ------------------------------------------------------------

def tracer_acwr(acwr_equipe, nom, lang="fr"):
    """Courbe ACWR interactive avec zones colorees."""
    donnees = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])

    titre = {"fr": "Ratio charge aigue / chronique",
             "en": "Acute / chronic load ratio"}
    hover_label = {"fr": "ACWR", "en": "ACWR"}

    figure = go.Figure()
    figure.add_hrect(y0=0.0, y1=0.8, fillcolor="#4A90D9", opacity=0.10, line_width=0)
    figure.add_hrect(y0=0.8, y1=1.3, fillcolor="#2E9E5B", opacity=0.12, line_width=0)
    figure.add_hrect(y0=1.3, y1=1.5, fillcolor="#E8A13C", opacity=0.12, line_width=0)
    figure.add_hrect(y0=1.5, y1=2.2, fillcolor="#D64545", opacity=0.10, line_width=0)

    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["acwr"],
            mode="lines", name=hover_label.get(lang, "ACWR"),
            line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>" + hover_label.get(lang, "ACWR") + " : %{y:.2f}<extra></extra>",
        ))

    figure.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[0, 2.2], title="ACWR"),
        title=titre.get(lang, titre["fr"]),
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


def tracer_hooper(df_bien_etre, nom, lang="fr"):
    """Courbe de l'indice de Hooper avec zones indicatives."""
    df = calculer_hooper(df_bien_etre)
    donnees = df[df["nom"] == nom].sort_values("date")

    titre = {"fr": "Bien-etre quotidien (plus bas = mieux)",
             "en": "Daily well-being (lower = better)"}
    hover_label = {"fr": "Hooper", "en": "Hooper"}
    yaxis_label = {"fr": "Indice de Hooper", "en": "Hooper index"}

    figure = go.Figure()
    figure.add_hrect(y0=4, y1=13, fillcolor="#2E9E5B", opacity=0.10, line_width=0)
    figure.add_hrect(y0=13, y1=19, fillcolor="#E8A13C", opacity=0.10, line_width=0)
    figure.add_hrect(y0=19, y1=28, fillcolor="#D64545", opacity=0.10, line_width=0)

    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["hooper"],
            mode="lines", line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>" + hover_label.get(lang, "Hooper") + " : %{y}<extra></extra>",
        ))

    figure.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[4, 28], title=yaxis_label.get(lang, yaxis_label["fr"])),
        title=titre.get(lang, titre["fr"]),
        showlegend=False,
    )
    return figure


def tracer_monotonie_contrainte(monotonie, nom, lang="fr"):
    """Deux courbes : monotonie et contrainte (axes separes)."""
    donnees = monotonie[monotonie["nom"] == nom].dropna(subset=["monotonie"])

    titre = {"fr": "Monotonie et contrainte (Foster)",
             "en": "Monotony and strain (Foster)"}
    label_monotonie = {"fr": "Monotonie", "en": "Monotony"}
    label_contrainte = {"fr": "Contrainte", "en": "Strain"}
    yaxis1_label = {"fr": "Monotonie", "en": "Monotony"}
    yaxis2_label = {"fr": "Contrainte (UA)", "en": "Strain (AU)"}
    annotation_text = {"fr": "Monotonie 2.0", "en": "Monotony 2.0"}

    figure = go.Figure()
    if len(donnees) > 0:
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["monotonie"],
            mode="lines", name=label_monotonie.get(lang, label_monotonie["fr"]),
            line=dict(color="#1B6B93", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>" + label_monotonie.get(lang, "Monotonie") + " : %{y:.2f}<extra></extra>",
        ))
        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["contrainte"],
            mode="lines", name=label_contrainte.get(lang, label_contrainte["fr"]), yaxis="y2",
            line=dict(color="#C77B3F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>" + label_contrainte.get(lang, "Contrainte") + " : %{y:.0f}<extra></extra>",
        ))
        figure.add_hline(y=2.0, line_dash="dot", line_color="#D64545",
                         annotation_text=annotation_text.get(lang, annotation_text["fr"]))

    figure.update_layout(
        height=320, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title=yaxis1_label.get(lang, yaxis1_label["fr"])),
        yaxis2=dict(title=yaxis2_label.get(lang, yaxis2_label["fr"]), overlaying="y", side="right"),
        title=titre.get(lang, titre["fr"]),
        legend=dict(orientation="h", y=1.15),
    )
    return figure


def tracer_sauts(sauts_hebdo, nom, lang="fr"):
    """Barres du volume hebdomadaire de sauts."""
    donnees = sauts_hebdo[sauts_hebdo["nom"] == nom]

    titre = {"fr": "Volume de sauts hebdomadaire",
             "en": "Weekly jump volume"}
    hover_label = {"fr": "sauts", "en": "jumps"}
    yaxis_label = {"fr": "Sauts / semaine", "en": "Jumps / week"}

    figure = go.Figure()
    if len(donnees) > 0:
        figure.add_trace(go.Bar(
            x=donnees["semaine"], y=donnees["sauts"],
            marker_color="#1B6B93", marker_line_color="#12303F",
            marker_line_width=1,
            hovertemplate="Semaine du %{x|%d/%m}<br>%{y} " + hover_label.get(lang, "sauts") + "<extra></extra>",
        ))

    figure.update_layout(
        height=280, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title=yaxis_label.get(lang, yaxis_label["fr"])),
        title=titre.get(lang, titre["fr"]),
    )
    return figure


def tracer_croissance(croissance, nom, lang="fr"):
    """Courbe de taille avec vitesse estimee en infobulle."""
    donnees = croissance[croissance["nom"] == nom].sort_values("date")

    titre = {"fr": "Croissance", "en": "Growth"}
    yaxis_label = {"fr": "Taille (cm)", "en": "Height (cm)"}
    text_premiere = {"fr": "Premiere mesure", "en": "First measurement"}
    text_vitesse = {"fr": "Vitesse", "en": "Velocity"}
    text_taille = {"fr": "Taille", "en": "Height"}

    figure = go.Figure()
    if len(donnees) > 0:
        textes = []
        for indice in range(len(donnees)):
            vitesse = donnees["vitesse_cm_an"].iloc[indice]
            if pd.isna(vitesse):
                textes.append(text_premiere.get(lang, text_premiere["fr"]))
            else:
                textes.append(text_vitesse.get(lang, "Vitesse") + " : "
                              + str(round(float(vitesse), 1)) + " cm/an")

        figure.add_trace(go.Scatter(
            x=donnees["date"], y=donnees["taille_cm"],
            mode="lines+markers", text=textes,
            line=dict(color="#12303F", width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>" + text_taille.get(lang, "Taille") + " : %{y} cm<br>%{text}<extra></extra>",
        ))

    figure.update_layout(
        height=280, margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title=yaxis_label.get(lang, yaxis_label["fr"])),
        title=titre.get(lang, titre["fr"]),
        showlegend=False,
    )
    return figure


# ------------------------------------------------------------
# AFFICHAGE DU CENTRE D'ALERTES
# ------------------------------------------------------------

def afficher_centre_alertes(depot):
    """Affiche les alertes construites par calculs.construire_toutes_alertes
    (fusion ACWR + individualisees, deja triees par gravite).
    Permet de marquer les alertes comme traitees avec une note."""
    toutes_alertes = construire_toutes_alertes(
        depot.seances(), depot.bien_etre(), depot.anthropometrie()
    )

    # Initialiser le suivi des alertes traitees
    if "alertes_vues" not in st.session_state:
        st.session_state["alertes_vues"] = {}

    if len(toutes_alertes) == 0:
        st.success(t("aucune_alerte"))
        return

    # Filtrer les alertes actives (non traitees)
    alertes_actives = []
    alertes_traitees = []
    for alerte in toutes_alertes:
        cle = _cle_alerte(alerte)
        if cle in st.session_state["alertes_vues"]:
            alertes_traitees.append(alerte)
        else:
            alertes_actives.append(alerte)

    st.subheader(t("centre_alertes", n=len(alertes_actives)))

    for alerte in alertes_actives:
        module_tr, message_tr = traduire_alerte(alerte)
        texte = ("**" + alerte["nom"] + "** · " + module_tr
                 + " — " + message_tr)
        if alerte["niveau"] == "alerte":
            st.error(texte)
        else:
            st.warning(texte)

        # Bouton marquer comme traitee avec note
        with st.expander(t("marquer_alerte"), expanded=False):
            note = st.text_input(
                t("note_alerte"),
                value=st.session_state["alertes_vues"].get(
                    _cle_alerte(alerte), {}).get("note", ""),
                key="note_" + _cle_alerte(alerte),
                placeholder=t("note_alerte_placeholder"),
            )
            if st.button(t("marquer_alerte"), key="btn_" + _cle_alerte(alerte)):
                st.session_state["alertes_vues"][_cle_alerte(alerte)] = {
                    "timestamp": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                    "note": note,
                    "nom": alerte["nom"],
                    "module": module_tr,
                    "message": message_tr,
                    "niveau": alerte["niveau"],
                }
                st.rerun()

    # Afficher les alertes traitees (grises, repliees)
    if alertes_traitees:
        with st.expander(t("alerte_traitee", n=len(alertes_traitees)), expanded=False):
            for alerte in alertes_traitees:
                cle = _cle_alerte(alerte)
                info = st.session_state["alertes_vues"].get(cle, {})
                st.markdown(
                    "~~**" + alerte["nom"] + "** · "
                    + info.get("module", "") + " — "
                    + info.get("message", "") + "~~"
                )
                if info.get("note"):
                    st.caption("📝 " + info["note"])
                st.caption("✓ " + info.get("timestamp", ""))


def _cle_alerte(alerte):
    """Genere une cle unique pour une alerte."""
    return alerte["nom"] + "_" + alerte["module"] + "_" + str(alerte.get("date", ""))


# ------------------------------------------------------------
# PAGE 1 — VUE D'EQUIPE
# ------------------------------------------------------------

def page_vue_equipe(depot):
    st.header(t("equipe_titre"))

    df = depot.seances()
    synthese, acwr_equipe = construire_synthese_equipe(df)

    colonne_a, colonne_b, colonne_c, colonne_d = st.columns(4)

    nb_joueuses = df["nom"].nunique()
    nb_seances = len(df.dropna(subset=["rpe", "duree_min"]))
    cmj_moyen = synthese["CMJ (cm)"].mean()

    colonne_a.metric(t("m_joueuses"), nb_joueuses)
    colonne_b.metric(t("m_seances"), nb_seances)

    if depot.bien_etre() is not None:
        matrice = bien_etre_du_jour(depot.bien_etre())
        hooper_moyen = matrice["Hooper"].mean()
        colonne_c.metric(t("m_hooper_jour"), round(hooper_moyen, 1))
    else:
        colonne_c.metric(t("m_hooper"), "—")

    if pd.notna(cmj_moyen):
        colonne_d.metric(t("m_cmj_equipe"), str(round(cmj_moyen, 1)) + " cm")
    else:
        colonne_d.metric(t("m_cmj_equipe"), "—")

    afficher_centre_alertes(depot)

    # --- Tableau de synthese --------------------------------
    st.subheader(t("synthese_joueuse"))

    tableau = synthese.copy()

    # Ajouter le bien-etre du jour si disponible
    if depot.bien_etre() is not None:
        matrice = bien_etre_du_jour(depot.bien_etre())
        hooper_par_joueuse = {}
        for indice in range(len(matrice)):
            hooper_par_joueuse[matrice["Joueuse"].iloc[indice]] = matrice["Etat"].iloc[indice]
        valeurs_bien_etre = []
        for indice in range(len(tableau)):
            nom = tableau["Joueuse"].iloc[indice]
            valeurs_bien_etre.append(hooper_par_joueuse.get(nom, "—"))
        tableau[t("col_bien_etre")] = valeurs_bien_etre

    tableau["CMJ (cm)"] = tableau["CMJ (cm)"].round(1)
    tableau["Attaque (cm)"] = tableau["Attaque (cm)"].round(0)
    tableau["Sprint 10 m (s)"] = tableau["Sprint 10 m (s)"].round(2)
    tableau["ACWR"] = tableau["ACWR"].round(2)
    st.dataframe(tableau, use_container_width=True, hide_index=True)

    # --- Disponibilite --------------------------------------
    if depot.blessures() is not None:
        st.subheader(t("disponibilite"))
        disponibilite = calculer_disponibilite(depot.blessures(), df)
        st.dataframe(disponibilite, use_container_width=True, hide_index=True)
        st.caption(t("dispo_note"))

    # --- Charge collective ----------------------------------
    st.subheader(t("charge_hebdo_equipe"))

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
        yaxis=dict(title=t("charge_ua")),
    )
    st.plotly_chart(figure, use_container_width=True)


# ------------------------------------------------------------
# PAGE 2 — BIEN-ETRE DU JOUR
# ------------------------------------------------------------

def page_bien_etre(depot):
    st.header(t("bien_etre_equipe"))

    if depot.bien_etre() is None:
        st.info(t("bien_etre_vide"))
        return

    matrice = bien_etre_du_jour(depot.bien_etre())

    st.subheader(t("matrice_jour"))
    st.caption(t("matrice_caption"))
    st.dataframe(matrice, use_container_width=True, hide_index=True)

    st.subheader(t("evolution_individuelle"))
    noms_disponibles = sorted(depot.bien_etre()["nom"].unique())
    nom = st.selectbox(t("joueuse"), noms_disponibles)
    st.plotly_chart(tracer_hooper(depot.bien_etre(), nom, langue_courante()),
                    use_container_width=True)

    # Detail des 4 composantes sur les 14 derniers jours
    st.subheader(t("detail_14j"))
    df = depot.bien_etre()
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

def page_fiche_joueuse(depot):
    st.header(t("fiche_titre"))

    df = depot.seances()
    noms_disponibles = sorted(df["nom"].unique())
    nom = st.selectbox(t("choisir_joueuse"), noms_disponibles)

    donnees_joueuse = df[df["nom"] == nom]
    poste = donnees_joueuse["poste"].iloc[-1]
    st.caption(t("poste") + " : " + poste)

    # --- Synthese instantanee (vue 360) ---------------------
    # Etat du jour de la joueuse avant tout detail : charge,
    # bien-etre, disponibilite et alertes actives.
    acwr_equipe = calculer_acwr_equipe(df)
    toutes_alertes = construire_toutes_alertes(
        df, depot.bien_etre(), depot.anthropometrie()
    )
    alertes_joueuse = []
    for alerte in toutes_alertes:
        if alerte["nom"] == nom:
            alertes_joueuse.append(alerte)

    colonne_a, colonne_b, colonne_c, colonne_d = st.columns(4)

    donnees_acwr = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])
    if len(donnees_acwr) > 0:
        acwr_actuel = float(donnees_acwr["acwr"].iloc[-1])
        cle_etiq, couleur_acwr, emoji_acwr = cle_acwr(acwr_actuel)
        colonne_a.metric(t("m_acwr"), emoji_acwr + " " + str(round(acwr_actuel, 2)),
                         help=etiquette_acwr(cle_etiq))
    else:
        colonne_a.metric(t("m_acwr"), "—",
                         help=t("m_acwr_help_insuffisant"))

    if depot.bien_etre() is not None:
        df_hooper = calculer_hooper(depot.bien_etre())
        reponses = df_hooper[df_hooper["nom"] == nom].sort_values("date")
        if len(reponses) > 0:
            hooper_jour = int(reponses["hooper"].iloc[-1])
            etiquette_h, emoji_h = interpreter_hooper(float(hooper_jour))
            colonne_b.metric(t("m_bien_etre_hooper"),
                             emoji_h + " " + str(hooper_jour),
                             help=etiquette_h + " — " + t("hooper_echelle"))
        else:
            colonne_b.metric(t("m_bien_etre_hooper"), "—")
    else:
        colonne_b.metric(t("m_bien_etre_hooper"), "—")

    if depot.blessures() is not None:
        disponibilite = calculer_disponibilite(depot.blessures(), df)
        ligne_dispo = disponibilite[disponibilite["Joueuse"] == nom]
        if len(ligne_dispo) > 0:
            colonne_c.metric(
                t("disponibilite"),
                str(ligne_dispo["Disponibilite (%)"].iloc[0]) + " %",
                help=t("episodes_help",
                       e=ligne_dispo["Episodes"].iloc[0],
                       j=ligne_dispo["Jours d'absence"].iloc[0]),
            )
        else:
            colonne_c.metric(t("disponibilite"), "—")
    else:
        colonne_c.metric(t("disponibilite"), "—")

    colonne_d.metric(t("m_alertes_actives"), str(len(alertes_joueuse)))

    if len(alertes_joueuse) > 0:
        for alerte in alertes_joueuse:
            module_tr, message_tr = traduire_alerte(alerte)
            texte = module_tr + " — " + message_tr
            if alerte["niveau"] == "alerte":
                st.error(texte)
            else:
                st.warning(texte)
    else:
        st.caption(t("aucune_alerte_joueuse"))

    # --- Progression sur les tests --------------------------
    progression = calculer_progression(df, nom)

    if len(progression) == 0:
        st.info(t("progression_insuffisante"))
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
        [t("onglet_tests"), t("onglet_charge"), t("onglet_bien_etre"),
         t("onglet_croissance"), t("onglet_blessures")]
    )

    with onglet_tests:
        choix_test = st.selectbox(
            t("indicateur"), COLONNES_TESTS,
            format_func=LIBELLES_TESTS.get,
        )
        st.plotly_chart(
            tracer_evolution_test(df, [nom], choix_test),
            use_container_width=True,
        )

    with onglet_charge:
        donnees_acwr = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])
        lang = langue_courante()

        if len(donnees_acwr) == 0:
            st.info(t("acwr_insuffisant"))
        else:
            acwr_actuel = float(donnees_acwr["acwr"].iloc[-1])
            etiquette, couleur, emoji = interpreter_acwr(acwr_actuel)
            st.markdown(emoji + " ACWR actuel : **"
                        + str(round(acwr_actuel, 2)) + "** — " + etiquette)
            st.plotly_chart(tracer_acwr(acwr_equipe, nom, lang),
                            use_container_width=True)

        monotonie = calculer_monotonie_contrainte(df)
        st.plotly_chart(tracer_monotonie_contrainte(monotonie, nom, lang),
                        use_container_width=True)

        sauts_hebdo = calculer_sauts_hebdo(df)
        if len(sauts_hebdo[sauts_hebdo["nom"] == nom]) > 0:
            st.plotly_chart(tracer_sauts(sauts_hebdo, nom, lang),
                            use_container_width=True)
        else:
            st.info(t("pas_sauts"))

    with onglet_bien_etre:
        if depot.bien_etre() is None:
            st.info(t("aucun_bien_etre"))
        else:
            df_be = depot.bien_etre()
            if len(df_be[df_be["nom"] == nom]) == 0:
                st.info(t("pas_reponses_joueuse"))
            else:
                st.plotly_chart(tracer_hooper(df_be, nom, langue_courante()),
                                use_container_width=True)

    with onglet_corps:
        if depot.anthropometrie() is None:
            st.info(t("aucune_anthro"))
        else:
            croissance = calculer_croissance(depot.anthropometrie())
            donnees_croissance = croissance[croissance["nom"] == nom]
            if len(donnees_croissance) == 0:
                st.info(t("pas_mesures_joueuse"))
            else:
                lang = langue_courante()
                derniere_vitesse = donnees_croissance["vitesse_cm_an"].dropna()
                if len(derniere_vitesse) > 0:
                    vitesse = float(derniere_vitesse.iloc[-1])
                    if vitesse > 7.0:
                        if lang == "en":
                            st.warning(
                                "Estimated growth velocity: "
                                + str(round(vitesse, 1))
                                + " cm/yr — likely growth spurt. "
                                + "Vigilance period: modulate load and jumps."
                            )
                        else:
                            st.warning(
                                "Vitesse de croissance estimee : "
                                + str(round(vitesse, 1))
                                + " cm/an — pic de croissance probable. "
                                + "Periode de vigilance : moduler charge et sauts."
                            )
                    else:
                        if lang == "en":
                            st.markdown("Estimated growth velocity: **"
                                        + str(round(vitesse, 1)) + " cm/yr**")
                        else:
                            st.markdown("Vitesse de croissance estimee : **"
                                        + str(round(vitesse, 1)) + " cm/an**")
                st.plotly_chart(tracer_croissance(croissance, nom, lang),
                                use_container_width=True)

    with onglet_blessures:
        if depot.blessures() is None:
            st.info(t("aucun_journal_blessures"))
        else:
            episodes = depot.blessures()[depot.blessures()["nom"] == nom]
            if len(episodes) == 0:
                st.success(t("aucun_episode_joueuse"))
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

def page_comparaison(depot):
    st.header(t("comparaison_titre"))

    df = depot.seances()
    noms_disponibles = sorted(df["nom"].unique())
    noms_choisis = st.multiselect(
        t("joueuses_comparer"), noms_disponibles,
        default=noms_disponibles[:3],
    )

    if len(noms_choisis) < 2:
        st.info(t("min_deux_joueuses"))
        return

    choix_test = st.selectbox(
        t("indicateur"), COLONNES_TESTS,
        format_func=LIBELLES_TESTS.get,
    )

    st.plotly_chart(
        tracer_evolution_test(df, noms_choisis, choix_test),
        use_container_width=True,
    )

    st.subheader(t("dernier_releve"))

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

def page_rapports(depot, nom_club):
    st.header(t("rapports_titre"))
    st.write(t("rapports_intro"))

    # Upload du logo (optionnel)
    logo_file = st.file_uploader(
        t("logo_club"),
        type=["png", "jpg", "jpeg"],
        help=t("logo_club_help"),
    )

    # Stocker le logo en session pour qu'il persiste entre les reruns
    if logo_file is not None:
        st.session_state["logo_club"] = logo_file.getvalue()

    logo_bytes = st.session_state.get("logo_club", None)

    df = depot.seances()
    nom_fichier_club = nom_club.lower().strip().replace(" ", "_")

    colonne_gauche, colonne_droite = st.columns(2)

    with colonne_gauche:
        st.subheader(t("fiche_individuelle"))
        noms_disponibles = sorted(df["nom"].unique())
        nom = st.selectbox(t("joueuse"), noms_disponibles)

        if st.button(t("generer_fiche"), type="primary"):
            with st.spinner(t("creation_pdf")):
                st.session_state["pdf_joueuse"] = generer_rapport_joueuse(
                    df, nom, nom_club, depot.bien_etre(),
                    lang=langue_courante(),
                    logo_bytes=logo_bytes,
                    alertes_vues=st.session_state.get("alertes_vues"),
                )
                st.session_state["pdf_joueuse_nom"] = nom

        # Le bouton de telechargement persiste apres le rerun Streamlit
        # (sinon il disparait des le premier clic)
        if (st.session_state.get("pdf_joueuse") is not None
                and st.session_state.get("pdf_joueuse_nom") == nom):
            st.download_button(
                t("telecharger_fiche", nom=nom),
                data=st.session_state["pdf_joueuse"],
                file_name="fiche_" + nom.replace(" ", "_") + ".pdf",
                mime="application/pdf",
            )

    with colonne_droite:
        st.subheader(t("synthese_equipe"))
        st.write(t("synthese_equipe_desc"))

        if st.button(t("generer_synthese"), type="primary"):
            with st.spinner(t("creation_pdf")):
                st.session_state["pdf_equipe"] = generer_rapport_equipe(
                    df, nom_club, lang=langue_courante(),
                    logo_bytes=logo_bytes,
                    alertes_vues=st.session_state.get("alertes_vues"),
                )

        if st.session_state.get("pdf_equipe") is not None:
            st.download_button(
                t("telecharger_synthese"),
                data=st.session_state["pdf_equipe"],
                file_name="synthese_equipe_" + nom_fichier_club + ".pdf",
                mime="application/pdf",
            )


# ------------------------------------------------------------
# PAGE 6 — METHODE
# ------------------------------------------------------------

def page_methode():
    lang = langue_courante()

    titre = {"fr": "Methode et references", "en": "Method and references"}
    st.header(titre.get(lang, titre["fr"]))

    if lang == "fr":
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
    else:
        st.markdown(
            """
**1. Training load — session-RPE method (Foster, 2001)**

Each session receives a load: `RPE (1-10) x duration in minutes`.
No sensors needed, only the perceived effort.

**2. ACWR — Acute:Chronic Workload Ratio**

Last 7 days' load divided by the weekly average of the last 28 days
(coupled rolling averages). The **0.80 - 1.30** zone is a descriptive
reference from the original literature (Gabbett, 2016), but the
individual predictive value of ACWR is now contested (Impellizzeri et
al., 2020). Here, ACWR is read as a **signal of unusual load variation**
that directs the coach's attention — not as an injury prediction.

**3. Monotony and strain (Foster)**

- Monotony = mean daily load / standard deviation (7 days).
  Above **2.0**: training too uniform, even at moderate load.
- Strain = weekly load x monotony. Assessed against each player's
  personal history (Z-score).

**4. Well-being — Hooper questionnaire (Hooper & Mackinnon, 1995)**

Each morning: sleep, fatigue, soreness and stress rated from
1 (very good) to 7 (very bad). Index = sum (4 to 28).
The thresholds shown (13 / 19) are indicative: the main reference
is each player's deviation from their own norm.

**5. Jump load**

Weekly jump volume, the volleyball-specific indicator (patellar
tendinopathy prevention). An increase of more than 50% compared to the
player's 4-week personal average triggers a watch.

**6. Growth**

Estimated velocity between measurements spaced at least 60 days apart.
Above approximately **7 cm/yr**: likely growth spurt, increased
vulnerability period (Lloyd & Oliver, 2012) — modulate load and jumps.

**7. Individualized alerts (Z-scores)**

Each player is compared to **her own baseline** rather than universal
thresholds: `Z = (value - personal mean) / standard deviation`.
Z above +1.5 triggers a watch, above +2.5 triggers an alert.

---

**Limitations.** These indicators guide the coach's attention;
they do not replace staff judgment or medical advice. The thresholds
come from studies on varied populations and should be interpreted
carefully with young athletes.

**References.** Foster et al. (2001) · Hooper & Mackinnon (1995) ·
Gabbett (2016) · Impellizzeri et al. (2019, 2020 — ACWR critique) ·
Lloyd & Oliver (2012) · Bahr & Visnes (patellar tendinopathy and
jump load).
            """
        )


# ------------------------------------------------------------
# PAGE — ONBOARDING / EMPTY STATE
# ------------------------------------------------------------

def afficher_onboarding():
    """Ecran d'accueil quand aucune donnee n'est chargee."""
    st.title(t("onboarding_bienvenue"))
    st.markdown(t("onboarding_intro"))
    st.divider()

    colonne_gauche, colonne_droite = st.columns(2)

    with colonne_gauche:
        st.subheader(t("onboarding_demo_titre"))
        st.write(t("onboarding_demo_desc"))
        if st.button(t("onboarding_charger_demo"), type="primary", use_container_width=True):
            st.query_params["demo"] = "true"
            st.rerun()

    with colonne_droite:
        st.subheader(t("onboarding_importer_titre"))
        st.write(t("onboarding_importer_desc"))

    st.divider()
    st.subheader(t("onboarding_guide_titre"))
    st.markdown(t("onboarding_guide_etape1"))
    st.markdown(t("onboarding_guide_etape2"))
    st.markdown(t("onboarding_guide_etape3"))

    st.divider()
    st.subheader(t("modeles_expander"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            t("modele_seances"), data=generer_modele_csv(),
            file_name="modele_seances.csv", mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            t("modele_bien_etre"), data=generer_modele_bien_etre(),
            file_name="modele_bien_etre.csv", mime="text/csv",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            t("modele_anthro"), data=generer_modele_anthropometrie(),
            file_name="modele_anthropometrie.csv", mime="text/csv",
            use_container_width=True,
        )
    with col4:
        st.download_button(
            t("modele_blessures"), data=generer_modele_blessures(),
            file_name="modele_blessures.csv", mime="text/csv",
            use_container_width=True,
        )


# ------------------------------------------------------------
# POINT D'ENTREE
# ------------------------------------------------------------

# ------------------------------------------------------------
# PAGE — SAISIE RAPIDE DE TESTS (Sprint 2)
# ------------------------------------------------------------

def page_saisie_rapide(depot, mode_demo, nom_club):
    st.header(t("saisie_titre"))
    st.write(t("saisie_intro"))

    noms = depot.noms_joueuses()
    if len(noms) == 0:
        st.info(t("saisie_aucune_joueuse"))
        return

    postes = depot.postes_par_joueuse()

    colonne_gauche, colonne_droite = st.columns(2)
    with colonne_gauche:
        libelle_choisi = st.selectbox(
            t("test_a_saisir"),
            [LIBELLES_TESTS[c] for c in COLONNES_TESTS],
        )
        colonne_test = None
        for cle in COLONNES_TESTS:
            if LIBELLES_TESTS[cle] == libelle_choisi:
                colonne_test = cle
                break
    with colonne_droite:
        date_test = st.date_input(t("date_test"), value=pd.Timestamp.today())

    st.caption(t("saisie_cellule_vide"))

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
                t("resultat") + " (" + libelle_choisi + ")",
                help=t("resultat_help"),
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
        st.error(t("saisie_erreurs", ok=len(valides), total=nb_saisis))
        for message in erreurs:
            st.write("• " + message)
        return

    if nb_saisis == 0:
        st.info(t("saisie_min_un"))
        return

    st.success(t("saisie_ok", ok=len(valides), total=nb_saisis))

    apercu = pd.DataFrame([{
        "Joueuse": v["nom"],
        "Date": pd.Timestamp(date_test).strftime("%d/%m/%Y"),
        libelle_choisi: v[colonne_test],
    } for v in valides])
    st.dataframe(apercu, use_container_width=True, hide_index=True)

    if st.button(t("saisie_enregistrer"), type="primary"):
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
        st.success(t("saisie_confirmee", n=nb))
        if mode_demo:
            st.warning(t("saisie_demo_avert"))
        nom_fichier = nom_club.lower().strip().replace(" ", "_")
        st.download_button(
            t("saisie_telecharger"),
            data=st.session_state.get("export_pret", b""),
            file_name="seances_" + nom_fichier + ".csv",
            mime="text/csv",
        )
        st.caption(t("saisie_recharger"))


def principal():
    donnees, page, nom_club, mode_demo = obtenir_donnees()
    depot = DepotDonnees_session(donnees)

    # Afficher l'onboarding si aucune seance n'est chargee ET
    # pas en mode auto-demo (sinon l'onboarding eclipse les donnees demo)
    params = st.query_params
    auto_demo = params.get("demo", "false").lower() == "true"

    if depot.seances() is None or len(depot.seances()) == 0:
        if not auto_demo:
            afficher_onboarding()
            return

    if mode_demo:
        st.info(
            t("banniere_demo")
        )

    if page == "Vue d'equipe":
        page_vue_equipe(depot)
    elif page == "Fiche joueuse":
        page_fiche_joueuse(depot)
    elif page == "Saisie rapide":
        page_saisie_rapide(depot, mode_demo, nom_club)
    elif page == "Bien-etre":
        page_bien_etre(depot)
    elif page == "Comparaison":
        page_comparaison(depot)
    elif page == "Rapports PDF":
        page_rapports(depot, nom_club)
    else:
        page_methode()

    st.sidebar.divider()
    with st.sidebar.expander(t("confid_titre")):
        st.markdown(t("confid_texte"))
    st.sidebar.caption(
        t("signature")
    )


principal()
