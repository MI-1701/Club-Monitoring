# ============================================================
# i18n.py — Internationalisation (FR / EN)
# ------------------------------------------------------------
# Source unique de tout le texte visible par l'utilisateur.
# Chaque chaine a une cle courte ; t(cle) renvoie la version
# dans la langue courante (stockee en session).
#
# Pour ajouter une langue : ajouter une colonne au dictionnaire.
# Pour ajouter une chaine : une entree {cle: {"fr": ..., "en": ...}}.
#
# Les messages dynamiques (alertes avec des nombres) utilisent
# des gabarits str.format : "{valeur}" est remplace a l'execution,
# donc les deux langues interpolent les memes donnees.
# ============================================================

import streamlit as st

LANGUES = {"fr": "Français", "en": "English"}
LANGUE_DEFAUT = "fr"


def langue_courante():
    """Langue active de la session (par defaut : francais)."""
    return st.session_state.get("langue", LANGUE_DEFAUT)


def t(cle, **kwargs):
    """Traduit une cle dans la langue courante.
    Les kwargs remplissent les gabarits {…} le cas echeant."""
    entree = TEXTES.get(cle)
    if entree is None:
        return cle  # cle manquante : visible en dev, jamais un crash
    texte = entree.get(langue_courante(), entree.get("fr", cle))
    if kwargs:
        try:
            return texte.format(**kwargs)
        except (KeyError, IndexError):
            return texte
    return texte


# ------------------------------------------------------------
# DICTIONNAIRE DES TEXTES
# ------------------------------------------------------------

TEXTES = {
    # --- Barre laterale / navigation ---
    "app_titre": {"fr": "Monitoring", "en": "Monitoring"},
    "nom_club_label": {"fr": "Nom du club / equipe",
                       "en": "Club / team name"},
    "nom_club_help": {
        "fr": "Ce nom apparait sur le dashboard et sur les rapports PDF.",
        "en": "This name appears on the dashboard and on PDF reports."},
    "monitoring_complet": {"fr": "Monitoring physique complet",
                           "en": "Complete physical monitoring"},
    "source_donnees": {"fr": "Source des donnees", "en": "Data source"},
    "source_demo": {"fr": "Donnees de demonstration",
                    "en": "Demonstration data"},
    "source_import": {"fr": "Importer mes fichiers CSV",
                      "en": "Import my CSV files"},
    "navigation": {"fr": "Navigation", "en": "Navigation"},
    "langue_label": {"fr": "Langue / Language",
                     "en": "Language / Langue"},

    # --- Pages (noms de nav) ---
    "page_equipe": {"fr": "Vue d'equipe", "en": "Team overview"},
    "page_fiche": {"fr": "Fiche joueuse", "en": "Player profile"},
    "page_saisie": {"fr": "Saisie rapide", "en": "Quick entry"},
    "page_bien_etre": {"fr": "Bien-etre", "en": "Well-being"},
    "page_comparaison": {"fr": "Comparaison", "en": "Comparison"},
    "page_rapports": {"fr": "Rapports PDF", "en": "PDF reports"},
    "page_methode": {"fr": "Methode", "en": "Method"},

    # --- Uploaders ---
    "up_seances": {"fr": "1. Seances (obligatoire)",
                   "en": "1. Sessions (required)"},
    "up_seances_help": {
        "fr": "Une ligne par seance et par joueuse : RPE, duree, sauts, "
              "tests. Taille max 10 Mo.",
        "en": "One row per session per player: RPE, duration, jumps, "
              "tests. Max size 10 MB."},
    "up_bien_etre": {"fr": "2. Bien-etre quotidien (optionnel)",
                     "en": "2. Daily well-being (optional)"},
    "up_bien_etre_help": {
        "fr": "Questionnaire matinal : sommeil, fatigue, courbatures, "
              "stress (1-7).",
        "en": "Morning questionnaire: sleep, fatigue, soreness, "
              "stress (1-7)."},
    "up_anthro": {"fr": "3. Anthropometrie (optionnel)",
                  "en": "3. Anthropometry (optional)"},
    "up_anthro_help": {"fr": "Mesures mensuelles : taille et masse.",
                       "en": "Monthly measurements: height and mass."},
    "up_blessures": {"fr": "4. Journal des blessures (optionnel)",
                     "en": "4. Injury log (optional)"},
    "up_blessures_help": {
        "fr": "Un episode par ligne : type, zone, jours d'absence.",
        "en": "One episode per row: type, area, days out."},
    "attente_seances": {
        "fr": "En attente du fichier de seances — les donnees de "
              "demonstration restent affichees.",
        "en": "Waiting for the sessions file — demonstration data "
              "stays displayed."},
    "seances_chargees": {
        "fr": "{n} seances chargees pour {j} joueuses.",
        "en": "{n} sessions loaded for {j} players."},

    # --- Modeles CSV ---
    "modeles_expander": {"fr": "Modeles CSV a telecharger",
                         "en": "CSV templates to download"},
    "modele_seances": {"fr": "Modele seances", "en": "Sessions template"},
    "modele_bien_etre": {"fr": "Modele bien-etre",
                         "en": "Well-being template"},
    "modele_anthro": {"fr": "Modele anthropometrie",
                      "en": "Anthropometry template"},
    "modele_blessures": {"fr": "Modele blessures",
                         "en": "Injuries template"},

    # --- Bandeau demo ---
    "banniere_demo": {
        "fr": "🟦 **Donnees de demonstration** — joueuses fictives. "
              "Passez a « Importer mes fichiers CSV » dans la barre "
              "laterale pour analyser vos propres donnees.",
        "en": "🟦 **Demonstration data** — fictional players. Switch to "
              "\"Import my CSV files\" in the sidebar to analyze your "
              "own data."},

    # --- Confidentialite ---
    "confid_titre": {"fr": "Confidentialite & securite",
                     "en": "Privacy & security"},
    "confid_texte": {
        "fr": "Les donnees importees sont **traitees en memoire pendant "
              "la session** ; l'application ne les persiste dans aucune "
              "base de donnees. Import limite a 10 Mo, fichiers valides "
              "avant analyse. L'hebergement (Streamlit Community Cloud) "
              "fournit le HTTPS.\n\nNe pas deposer de donnees reelles "
              "d'athletes mineures sur la demonstration publique.",
        "en": "Imported data is **processed in memory during the "
              "session**; the app does not persist it in any database. "
              "Uploads capped at 10 MB, files validated before analysis. "
              "Hosting (Streamlit Community Cloud) provides HTTPS.\n\nDo "
              "not upload real minor-athlete data to the public demo."},
    "signature": {
        "fr": "Concu par Ilias Moudrikah · seance-RPE · ACWR · Hooper "
              "· Z-scores",
        "en": "Built by Ilias Moudrikah · session-RPE · ACWR · Hooper "
              "· Z-scores"},

    # --- Vue d'equipe ---
    "equipe_titre": {"fr": "Vue d'equipe", "en": "Team overview"},
    "m_joueuses": {"fr": "Joueuses suivies", "en": "Players tracked"},
    "m_seances": {"fr": "Seances enregistrees",
                  "en": "Sessions recorded"},
    "m_hooper_jour": {"fr": "Hooper moyen (dernier jour)",
                      "en": "Mean Hooper (last day)"},
    "m_hooper": {"fr": "Hooper moyen", "en": "Mean Hooper"},
    "m_cmj_equipe": {"fr": "CMJ moyen equipe", "en": "Team mean CMJ"},
    "synthese_joueuse": {"fr": "Synthese par joueuse",
                         "en": "Per-player summary"},
    "col_bien_etre": {"fr": "Bien-etre", "en": "Well-being"},
    "disponibilite": {"fr": "Disponibilite", "en": "Availability"},
    "dispo_note": {
        "fr": "Jours d'absence recadres sur la periode des seances ; "
              "les episodes qui se chevauchent ne sont comptes qu'une "
              "fois.",
        "en": "Days out clipped to the sessions period; overlapping "
              "episodes are counted only once."},
    "charge_hebdo_equipe": {"fr": "Charge hebdomadaire de l'equipe",
                            "en": "Team weekly load"},
    "charge_ua": {"fr": "Charge (unites arbitraires)",
                  "en": "Load (arbitrary units)"},

    # --- Centre d'alertes ---
    "centre_alertes": {"fr": "Centre d'alertes ({n})",
                       "en": "Alert center ({n})"},
    "aucune_alerte": {
        "fr": "Aucune alerte : tous les indicateurs sont dans les normes.",
        "en": "No alerts: all indicators are within normal ranges."},

    # --- Fiche joueuse ---
    "fiche_titre": {"fr": "Fiche joueuse", "en": "Player profile"},
    "choisir_joueuse": {"fr": "Choisir une joueuse",
                        "en": "Choose a player"},
    "poste": {"fr": "Poste", "en": "Position"},
    "m_acwr": {"fr": "ACWR", "en": "ACWR"},
    "m_acwr_help_insuffisant": {
        "fr": "Historique insuffisant (28 jours)",
        "en": "Insufficient history (28 days)"},
    "m_bien_etre_hooper": {"fr": "Bien-etre (Hooper)",
                           "en": "Well-being (Hooper)"},
    "hooper_echelle": {"fr": "echelle 4 (excellent) a 28",
                       "en": "scale 4 (excellent) to 28"},
    "m_alertes_actives": {"fr": "Alertes actives", "en": "Active alerts"},
    "aucune_alerte_joueuse": {
        "fr": "Aucune alerte active pour cette joueuse.",
        "en": "No active alerts for this player."},
    "episodes_help": {"fr": "{e} episode(s), {j} jour(s) d'absence",
                      "en": "{e} episode(s), {j} day(s) out"},
    "progression_insuffisante": {
        "fr": "Pas encore assez de tests pour mesurer une progression "
              "(2 releves minimum par indicateur).",
        "en": "Not enough tests yet to measure progression "
              "(minimum 2 records per indicator)."},

    # --- Onglets fiche ---
    "onglet_tests": {"fr": "Tests", "en": "Tests"},
    "onglet_charge": {"fr": "Charge", "en": "Load"},
    "onglet_bien_etre": {"fr": "Bien-etre", "en": "Well-being"},
    "onglet_croissance": {"fr": "Croissance", "en": "Growth"},
    "onglet_blessures": {"fr": "Blessures", "en": "Injuries"},
    "indicateur": {"fr": "Indicateur", "en": "Indicator"},
    "acwr_actuel": {"fr": "ACWR actuel", "en": "Current ACWR"},
    "acwr_insuffisant": {
        "fr": "Historique insuffisant pour l'ACWR (28 jours de seances "
              "minimum).",
        "en": "Insufficient history for ACWR (minimum 28 days of "
              "sessions)."},
    "pas_sauts": {
        "fr": "Pas de donnees de sauts pour cette joueuse (colonne "
              "« sauts » du fichier seances).",
        "en": "No jump data for this player (\"sauts\" column of the "
              "sessions file)."},
    "aucun_bien_etre": {"fr": "Aucune donnee de bien-etre importee.",
                        "en": "No well-being data imported."},
    "pas_reponses_joueuse": {"fr": "Pas de reponses pour cette joueuse.",
                             "en": "No responses for this player."},
    "aucune_anthro": {"fr": "Aucune donnee anthropometrique importee.",
                      "en": "No anthropometric data imported."},
    "pas_mesures_joueuse": {"fr": "Pas de mesures pour cette joueuse.",
                            "en": "No measurements for this player."},
    "vitesse_croissance": {"fr": "Vitesse de croissance estimee",
                           "en": "Estimated growth velocity"},
    "aucun_journal_blessures": {"fr": "Aucun journal de blessures importe.",
                                "en": "No injury log imported."},
    "aucun_episode_joueuse": {
        "fr": "Aucun episode enregistre pour cette joueuse.",
        "en": "No episode recorded for this player."},
    "col_debut": {"fr": "Debut", "en": "Start"},
    "col_type": {"fr": "Type", "en": "Type"},
    "col_zone": {"fr": "Zone", "en": "Area"},
    "col_jours_absence": {"fr": "Jours d'absence", "en": "Days out"},

    # --- Bien-etre (page) ---
    "bien_etre_equipe": {"fr": "Bien-etre de l'equipe",
                         "en": "Team well-being"},
    "bien_etre_vide": {
        "fr": "Aucune donnee de bien-etre importee. Telechargez le "
              "modele dans la barre laterale : chaque joueuse note "
              "chaque matin son sommeil, sa fatigue, ses courbatures et "
              "son stress de 1 (tres bien) a 7 (tres mauvais).",
        "en": "No well-being data imported. Download the template in "
              "the sidebar: each player rates her sleep, fatigue, "
              "soreness and stress every morning from 1 (very good) to "
              "7 (very bad)."},
    "matrice_jour": {"fr": "Matrice du jour", "en": "Today's matrix"},
    "matrice_caption": {
        "fr": "Dernieres reponses de chaque joueuse. Echelle 1 (tres "
              "bien) a 7 (tres mauvais).",
        "en": "Latest responses per player. Scale 1 (very good) to 7 "
              "(very bad)."},
    "evolution_individuelle": {"fr": "Evolution individuelle",
                               "en": "Individual trend"},
    "joueuse": {"fr": "Joueuse", "en": "Player"},
    "detail_14j": {"fr": "Detail des 14 derniers jours",
                   "en": "Last 14 days detail"},

    # --- Comparaison ---
    "comparaison_titre": {"fr": "Comparaison entre joueuses",
                          "en": "Player comparison"},
    "joueuses_comparer": {"fr": "Joueuses a comparer",
                          "en": "Players to compare"},
    "min_deux_joueuses": {"fr": "Selectionnez au moins deux joueuses.",
                          "en": "Select at least two players."},
    "dernier_releve": {"fr": "Dernier releve par joueuse",
                       "en": "Latest record per player"},
    "col_date": {"fr": "Date", "en": "Date"},
    "col_valeur": {"fr": "Valeur", "en": "Value"},

    # --- Saisie rapide ---
    "saisie_titre": {"fr": "Saisie rapide d'un test",
                     "en": "Quick test entry"},
    "saisie_intro": {
        "fr": "Enregistrez un test pour toute l'equipe en une fois. La "
              "validation est atomique : tant qu'une valeur est "
              "invalide, rien n'est enregistre.",
        "en": "Record a test for the whole team at once. Validation is "
              "atomic: as long as one value is invalid, nothing is "
              "saved."},
    "saisie_aucune_joueuse": {
        "fr": "Aucune joueuse disponible. Chargez d'abord des seances.",
        "en": "No players available. Load sessions first."},
    "test_a_saisir": {"fr": "Test a saisir", "en": "Test to enter"},
    "date_test": {"fr": "Date du test", "en": "Test date"},
    "saisie_cellule_vide": {
        "fr": "Laissez une cellule vide pour une joueuse non testee ce "
              "jour.",
        "en": "Leave a cell empty for a player not tested that day."},
    "resultat": {"fr": "Resultat", "en": "Result"},
    "resultat_help": {"fr": "Valeur mesuree ; vide si non teste.",
                      "en": "Measured value; empty if not tested."},
    "saisie_erreurs": {
        "fr": "⚠ {ok}/{total} valeur(s) valide(s) — corrigez avant "
              "d'enregistrer :",
        "en": "⚠ {ok}/{total} valid value(s) — fix before saving:"},
    "saisie_min_un": {
        "fr": "Saisissez au moins un resultat pour continuer.",
        "en": "Enter at least one result to continue."},
    "saisie_ok": {
        "fr": "✓ {ok}/{total} valeur(s) valide(s). Apercu avant "
              "enregistrement :",
        "en": "✓ {ok}/{total} valid value(s). Preview before saving:"},
    "saisie_enregistrer": {"fr": "Enregistrer ces resultats",
                           "en": "Save these results"},
    "saisie_confirmee": {
        "fr": "{n} resultat(s) ajoute(s) a la session. Ils apparaissent "
              "immediatement dans les fiches et alertes.",
        "en": "{n} result(s) added to the session. They appear "
              "immediately in profiles and alerts."},
    "saisie_demo_avert": {
        "fr": "Mode demonstration : ces valeurs restent en memoire de "
              "session. Telechargez le CSV mis a jour pour les "
              "conserver et le recharger ensuite en mode import.",
        "en": "Demonstration mode: these values stay in session memory. "
              "Download the updated CSV to keep them and re-import "
              "later."},
    "saisie_telecharger": {"fr": "📥 Telecharger le CSV seances mis a jour",
                           "en": "📥 Download updated sessions CSV"},
    "saisie_recharger": {
        "fr": "Rechargez ce fichier via « Importer mes fichiers CSV » a "
              "la prochaine session pour retrouver ces resultats.",
        "en": "Re-import this file via \"Import my CSV files\" next "
              "session to restore these results."},

    # --- Rapports PDF ---
    "rapports_titre": {"fr": "Rapports PDF", "en": "PDF reports"},
    "rapports_intro": {
        "fr": "Generez un rapport pret a partager avec le staff, les "
              "parents ou la direction du club.",
        "en": "Generate a report ready to share with staff, parents or "
              "club management."},
    "fiche_individuelle": {"fr": "Fiche individuelle",
                           "en": "Individual sheet"},
    "generer_fiche": {"fr": "Generer la fiche", "en": "Generate sheet"},
    "creation_pdf": {"fr": "Creation du PDF en cours...",
                     "en": "Creating PDF..."},
    "telecharger_fiche": {"fr": "📄 Telecharger la fiche de {nom}",
                          "en": "📄 Download {nom}'s sheet"},
    "synthese_equipe": {"fr": "Synthese d'equipe", "en": "Team summary"},
    "synthese_equipe_desc": {
        "fr": "Tableau complet + alertes de charge, sur une page.",
        "en": "Full table + load alerts, on one page."},
    "generer_synthese": {"fr": "Generer la synthese",
                         "en": "Generate summary"},
    "telecharger_synthese": {"fr": "📄 Telecharger la synthese d'equipe",
                             "en": "📄 Download team summary"},
}


# ------------------------------------------------------------
# ALERTES — gabarits traduisibles
# ------------------------------------------------------------
# Les cles correspondent au module d'alerte ; chaque gabarit
# recoit les memes variables dans les deux langues.

TEXTES_ALERTES = {
    "acwr": {
        "fr": "ACWR a {valeur} : {etiquette}.",
        "en": "ACWR at {valeur}: {etiquette}."},
    "bien_etre": {
        "fr": "Indice de Hooper a {valeur} (Z = +{z} vs sa reference "
              "28 j) : etat degrade.",
        "en": "Hooper index at {valeur} (Z = +{z} vs 28-day baseline): "
              "degraded state."},
    "monotonie": {
        "fr": "Monotonie a {valeur} (> 2) : entrainement trop uniforme, "
              "varier les charges.",
        "en": "Monotony at {valeur} (> 2): training too uniform, vary "
              "the loads."},
    "contrainte": {
        "fr": "Contrainte hebdomadaire inhabituellement elevee (Z = +{z} "
              "vs sa reference 28 j).",
        "en": "Unusually high weekly strain (Z = +{z} vs 28-day "
              "baseline)."},
    "sauts": {
        "fr": "Volume de sauts a {valeur} cette semaine (moyenne 4 sem. "
              ": {moyenne}) : surveiller les genoux.",
        "en": "Jump volume at {valeur} this week (4-week mean: "
              "{moyenne}): watch the knees."},
    "cmj": {
        "fr": "CMJ a {valeur} cm, en dessous de sa reference (Z = {z}) : "
              "fatigue neuromusculaire possible.",
        "en": "CMJ at {valeur} cm, below baseline (Z = {z}): possible "
              "neuromuscular fatigue."},
    "croissance": {
        "fr": "Vitesse de croissance estimee a {valeur} cm/an : pic de "
              "croissance probable, moduler charge et sauts.",
        "en": "Estimated growth velocity {valeur} cm/yr: likely growth "
              "spurt, modulate load and jumps."},
}


def t_alerte(module, **kwargs):
    """Traduit un message d'alerte par son module."""
    entree = TEXTES_ALERTES.get(module)
    if entree is None:
        return module
    texte = entree.get(langue_courante(), entree.get("fr", module))
    try:
        return texte.format(**kwargs)
    except (KeyError, IndexError):
        return texte


# ------------------------------------------------------------
# ETIQUETTES ACWR (reutilisees dans alertes + statut)
# ------------------------------------------------------------

ETIQUETTES_ACWR = {
    "insuffisant": {"fr": "Donnees insuffisantes",
                    "en": "Insufficient data"},
    "baisse": {"fr": "Charge en baisse marquee",
               "en": "Marked load decrease"},
    "habituelle": {"fr": "Zone habituelle", "en": "Usual zone"},
    "vigilance": {"fr": "Vigilance", "en": "Watch"},
    "hausse": {"fr": "Hausse forte — vigilance accrue",
               "en": "Sharp increase — heightened watch"},
}


def etiquette_acwr(cle):
    entree = ETIQUETTES_ACWR.get(cle, ETIQUETTES_ACWR["insuffisant"])
    return entree.get(langue_courante(), entree["fr"])


# ------------------------------------------------------------
# TRADUCTION D'UNE ALERTE COMPLETE
# ------------------------------------------------------------
# Noms de module traduits (l'etiquette « · Module — » du centre
# d'alertes) et corps du message via les gabarits.

MODULES_ALERTES = {
    "ACWR": {"fr": "ACWR", "en": "ACWR"},
    "Bien-etre": {"fr": "Bien-etre", "en": "Well-being"},
    "Monotonie": {"fr": "Monotonie", "en": "Monotony"},
    "Contrainte": {"fr": "Contrainte", "en": "Strain"},
    "Sauts": {"fr": "Sauts", "en": "Jumps"},
    "CMJ": {"fr": "CMJ", "en": "CMJ"},
    "Croissance": {"fr": "Croissance", "en": "Growth"},
}


def module_alerte(module):
    entree = MODULES_ALERTES.get(module, {"fr": module, "en": module})
    return entree.get(langue_courante(), module)


def traduire_alerte(alerte):
    """Retourne (module_traduit, message_traduit) pour une alerte
    structuree (avec 'cle' et 'params'). Repli sur le message
    francais existant si la structure manque."""
    module_tr = module_alerte(alerte.get("module", ""))

    cle = alerte.get("cle")
    if cle is None:
        return module_tr, alerte.get("message", "")

    params = dict(alerte.get("params", {}))
    # L'alerte ACWR contient une etiquette a traduire elle-meme
    if cle == "acwr" and "cle_etiquette" in params:
        params["etiquette"] = etiquette_acwr(params.pop("cle_etiquette"))

    return module_tr, t_alerte(cle, **params)
