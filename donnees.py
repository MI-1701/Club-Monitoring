# ============================================================
# donnees.py — Gestion des donnees du dashboard FUS-VB
# ------------------------------------------------------------
# Ce module contient 3 responsabilites :
#   1. Generer un jeu de donnees de demonstration (anonymise)
#   2. Fournir le modele CSV vide a telecharger
#   3. Valider un fichier CSV importe par l'utilisateur
# ============================================================

import io
import numpy as np
import pandas as pd

# ------------------------------------------------------------
# 1. CONSTANTES DU MODELE DE DONNEES
# ------------------------------------------------------------
# Chaque ligne du CSV = une seance d'entrainement pour une joueuse.
# Les colonnes de tests physiques peuvent rester vides :
# les tests ne sont faits que toutes les 2 semaines environ.

COLONNES_OBLIGATOIRES = ["date", "nom", "poste", "rpe", "duree_min"]

COLONNES_TESTS = [
    "cmj_cm", "detente_attaque_cm", "detente_contre_cm",
    "vitesse_10m_s", "t_test_s", "medecine_ball_cm", "navette_s",
]

# sauts = nombre de sauts de la seance (optionnel, charge specifique volley)
TOUTES_COLONNES = COLONNES_OBLIGATOIRES + ["sauts"] + COLONNES_TESTS

# Libelles affiches dans l'interface (francais lisible)
LIBELLES_TESTS = {
    "cmj_cm": "Detente verticale CMJ (cm)",
    "detente_attaque_cm": "Detente d'attaque (cm touches)",
    "detente_contre_cm": "Detente de contre (cm touches)",
    "vitesse_10m_s": "Sprint 10 m (s)",
    "t_test_s": "T-test agilite (s)",
    "medecine_ball_cm": "Lancer medecine-ball (cm)",
    "navette_s": "Navette volleyball (s)",
}

# Pour chaque test : True si une valeur PLUS HAUTE est meilleure
SENS_AMELIORATION = {
    "cmj_cm": True,
    "detente_attaque_cm": True,
    "detente_contre_cm": True,
    "vitesse_10m_s": False,
    "t_test_s": False,
    "medecine_ball_cm": True,
    "navette_s": False,
}

POSTES_VALIDES = [
    "Passeuse", "Attaquante", "Centrale", "Libero", "Pointue", "Receptionneuse"
]


# ------------------------------------------------------------
# 2. JEU DE DONNEES DE DEMONSTRATION
# ------------------------------------------------------------
# 8 joueuses anonymisees, 16 semaines de saison, 4 seances/semaine.
# Les valeurs sont realistes pour des volleyeuses U17 et incluent
# une progression + du bruit aleatoire (graine fixe = reproductible).

def generer_donnees_demo():
    """Construit le DataFrame de demonstration complet."""
    graine = np.random.default_rng(17)

    noms = [
        "Joueuse 1", "Joueuse 2", "Joueuse 3", "Joueuse 4",
        "Joueuse 5", "Joueuse 6", "Joueuse 7", "Joueuse 8",
    ]
    postes = [
        "Passeuse", "Attaquante", "Centrale", "Libero",
        "Pointue", "Attaquante", "Centrale", "Receptionneuse",
    ]

    # Valeurs de depart par joueuse (niveau initial legerement different)
    cmj_depart = [34.0, 38.5, 36.0, 31.5, 39.0, 37.0, 35.5, 33.0]
    vit_depart = [2.05, 1.95, 2.00, 1.92, 1.93, 1.98, 2.02, 2.08]
    mb_depart = [520.0, 610.0, 640.0, 480.0, 630.0, 590.0, 615.0, 505.0]
    nav_depart = [11.8, 11.2, 11.5, 10.9, 11.0, 11.3, 11.6, 12.0]
    att_depart = [258.0, 274.0, 265.0, 249.0, 277.0, 268.0, 271.0, 254.0]
    ctr_depart = [244.0, 259.0, 251.0, 236.0, 262.0, 254.0, 257.0, 240.0]
    ttest_depart = [11.4, 10.9, 11.1, 10.6, 10.8, 11.0, 11.2, 11.6]

    date_debut = pd.Timestamp("2026-03-02")  # un lundi
    jours_seances = [0, 1, 3, 5]  # lundi, mardi, jeudi, samedi
    nb_semaines = 16

    lignes = []

    for i in range(len(noms)):
        # Facteur de progression individuel sur toute la saison
        progression = graine.uniform(0.06, 0.14)

        for semaine in range(nb_semaines):
            # Charge planifiee : montee progressive avec une semaine
            # de decharge toutes les 4 semaines (periodisation classique).
            # La toute derniere semaine n'est jamais une decharge, pour
            # que la vue "actuelle" de la demo reste representative.
            est_decharge = (semaine + 1) % 4 == 0 and semaine != nb_semaines - 1
            if est_decharge:
                intensite_semaine = 0.65  # semaine de decharge
            else:
                intensite_semaine = 0.85 + 0.05 * (semaine % 4)

            # La joueuse 5 subit un pic de charge brutal sur la
            # derniere semaine (montee trop rapide avant un tournoi) :
            # la demo affiche ainsi une alerte ACWR immediatement visible.
            if i == 4 and semaine == nb_semaines - 1:
                intensite_semaine = 1.65

            # Variabilite individuelle realiste d'une semaine a l'autre
            intensite_semaine = intensite_semaine + graine.normal(0, 0.07)

            for jour in jours_seances:
                date_seance = date_debut + pd.Timedelta(days=semaine * 7 + jour)

                # RPE entre 3 et 9 selon l'intensite de la semaine
                rpe_base = 4.0 + 4.0 * intensite_semaine
                rpe = round(float(np.clip(graine.normal(rpe_base, 0.8), 3, 10)))

                # Duree entre 60 et 120 minutes
                duree_base = 75 + 30 * intensite_semaine
                duree = int(np.clip(graine.normal(duree_base, 10), 60, 130))

                # Nombre de sauts : depend du poste et de l'intensite.
                # Le libero saute tres peu, les centrales le plus.
                sauts_base_par_poste = {
                    "Passeuse": 45, "Attaquante": 50, "Centrale": 55,
                    "Libero": 8, "Pointue": 50, "Receptionneuse": 40,
                }
                sauts_base = sauts_base_par_poste[postes[i]]
                sauts = int(np.clip(
                    graine.normal(sauts_base * intensite_semaine, 8), 0, 140
                ))

                ligne = {
                    "date": date_seance,
                    "nom": noms[i],
                    "poste": postes[i],
                    "rpe": rpe,
                    "duree_min": duree,
                    "sauts": sauts,
                    "cmj_cm": np.nan,
                    "detente_attaque_cm": np.nan,
                    "detente_contre_cm": np.nan,
                    "t_test_s": np.nan,
                    "vitesse_10m_s": np.nan,
                    "medecine_ball_cm": np.nan,
                    "navette_s": np.nan,
                }

                # Tests physiques : le lundi, toutes les 2 semaines
                if jour == 0 and semaine % 2 == 0:
                    avancement = semaine / nb_semaines

                    cmj = cmj_depart[i] * (1 + progression * avancement)
                    cmj = cmj + graine.normal(0, 0.5)

                    vit = vit_depart[i] * (1 - progression * 0.6 * avancement)
                    vit = vit + graine.normal(0, 0.02)

                    mb = mb_depart[i] * (1 + progression * 1.2 * avancement)
                    mb = mb + graine.normal(0, 8)

                    nav = nav_depart[i] * (1 - progression * 0.5 * avancement)
                    nav = nav + graine.normal(0, 0.08)

                    att = att_depart[i] * (1 + progression * 0.25 * avancement)
                    att = att + graine.normal(0, 1.2)

                    ctr = ctr_depart[i] * (1 + progression * 0.25 * avancement)
                    ctr = ctr + graine.normal(0, 1.2)

                    ttest = ttest_depart[i] * (1 - progression * 0.4 * avancement)
                    ttest = ttest + graine.normal(0, 0.10)

                    ligne["detente_attaque_cm"] = round(float(att), 0)
                    ligne["detente_contre_cm"] = round(float(ctr), 0)
                    ligne["t_test_s"] = round(float(ttest), 2)
                    ligne["cmj_cm"] = round(float(cmj), 1)
                    ligne["vitesse_10m_s"] = round(float(vit), 2)
                    ligne["medecine_ball_cm"] = round(float(mb), 0)
                    ligne["navette_s"] = round(float(nav), 2)

                lignes.append(ligne)

    df = pd.DataFrame(lignes)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["nom", "date"]).reset_index(drop=True)
    return df


# ------------------------------------------------------------
# 3. MODELE CSV A TELECHARGER
# ------------------------------------------------------------

def generer_modele_csv():
    """Retourne le contenu texte du modele CSV avec 3 lignes d'exemple."""
    exemples = [
        {
            "date": "2026-09-07", "nom": "Salma B.", "poste": "Attaquante",
            "rpe": 7, "duree_min": 90, "sauts": 52, "cmj_cm": 36.5,
            "detente_attaque_cm": 266, "detente_contre_cm": 252,
            "vitesse_10m_s": 1.98, "t_test_s": 11.0,
            "medecine_ball_cm": 590, "navette_s": 11.4,
        },
        {
            "date": "2026-09-08", "nom": "Salma B.", "poste": "Attaquante",
            "rpe": 6, "duree_min": 75, "sauts": 38, "cmj_cm": "",
            "detente_attaque_cm": "", "detente_contre_cm": "",
            "vitesse_10m_s": "", "t_test_s": "",
            "medecine_ball_cm": "", "navette_s": "",
        },
        {
            "date": "2026-09-07", "nom": "Aya K.", "poste": "Libero",
            "rpe": 5, "duree_min": 90, "sauts": 6, "cmj_cm": 31.0,
            "detente_attaque_cm": 251, "detente_contre_cm": 238,
            "vitesse_10m_s": 1.94, "t_test_s": 10.7,
            "medecine_ball_cm": 470, "navette_s": 10.8,
        },
    ]
    df = pd.DataFrame(exemples, columns=TOUTES_COLONNES)
    tampon = io.StringIO()
    df.to_csv(tampon, index=False)
    return tampon.getvalue()


# ------------------------------------------------------------
# 4. VALIDATION D'UN CSV IMPORTE
# ------------------------------------------------------------
# Retourne (DataFrame propre, liste d'erreurs, liste d'avertissements).
# Si la liste d'erreurs n'est pas vide, le fichier est rejete.

def valider_csv(fichier):
    """Lit et valide le CSV envoye par l'utilisateur."""
    erreurs = []
    avertissements = []

    try:
        df = pd.read_csv(fichier)
    except Exception as probleme:
        erreurs.append("Fichier illisible : " + str(probleme))
        return None, erreurs, avertissements

    # Normaliser les noms de colonnes (minuscules, sans espaces)
    nouvelles_colonnes = []
    for colonne in df.columns:
        nouvelles_colonnes.append(str(colonne).strip().lower())
    df.columns = nouvelles_colonnes

    # Verifier les colonnes obligatoires
    for colonne in COLONNES_OBLIGATOIRES:
        if colonne not in df.columns:
            erreurs.append("Colonne obligatoire manquante : « " + colonne + " »")

    if len(erreurs) > 0:
        return None, erreurs, avertissements

    # Ajouter les colonnes de tests absentes (vides)
    for colonne in COLONNES_TESTS + ["sauts"]:
        if colonne not in df.columns:
            df[colonne] = np.nan
            avertissements.append(
                "Colonne « " + colonne + " » absente : ajoutee vide."
            )

    # Conversion des dates
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    nb_dates_invalides = int(df["date"].isna().sum())
    if nb_dates_invalides > 0:
        avertissements.append(
            str(nb_dates_invalides)
            + " ligne(s) avec date invalide supprimee(s). Format attendu : AAAA-MM-JJ."
        )
        df = df.dropna(subset=["date"])

    # Conversion des colonnes numeriques
    colonnes_numeriques = ["rpe", "duree_min", "sauts"] + COLONNES_TESTS
    for colonne in colonnes_numeriques:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    # RPE et duree sont obligatoires pour le calcul de charge
    nb_charge_invalide = int(df["rpe"].isna().sum() + df["duree_min"].isna().sum())
    if nb_charge_invalide > 0:
        avertissements.append(
            "Certaines lignes n'ont pas de RPE ou de duree : "
            + "elles seront ignorees dans le calcul de la charge."
        )

    # Bornes de coherence : les valeurs impossibles sont exclues des
    # calculs (mises a NaN) plutot que silencieusement conservees
    masque_rpe = df["rpe"].notna() & ((df["rpe"] < 1) | (df["rpe"] > 10))
    if masque_rpe.sum() > 0:
        avertissements.append(
            str(int(masque_rpe.sum()))
            + " valeur(s) de RPE hors de l'echelle 1-10 : "
            + "exclue(s) du calcul de charge."
        )
        df.loc[masque_rpe, "rpe"] = np.nan

    masque_duree = df["duree_min"].notna() & (df["duree_min"] <= 0)
    if masque_duree.sum() > 0:
        avertissements.append(
            str(int(masque_duree.sum()))
            + " duree(s) nulle(s) ou negative(s) : "
            + "exclue(s) du calcul de charge."
        )
        df.loc[masque_duree, "duree_min"] = np.nan

    masque_sauts = df["sauts"].notna() & (df["sauts"] < 0)
    if masque_sauts.sum() > 0:
        avertissements.append(
            str(int(masque_sauts.sum()))
            + " nombre(s) de sauts negatif(s) : exclu(s)."
        )
        df.loc[masque_sauts, "sauts"] = np.nan

    # Dates dans le futur : probable erreur de saisie (avertir sans rejeter)
    limite_future = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    nb_futures = int((df["date"] > limite_future).sum())
    if nb_futures > 0:
        avertissements.append(
            str(nb_futures) + " ligne(s) datee(s) dans le futur : "
            + "verifiez les dates de seance."
        )

    # Nettoyage des textes
    df["nom"] = df["nom"].astype(str).str.strip()
    df["poste"] = df["poste"].astype(str).str.strip()

    # Noms vides : lignes inexploitables
    masque_nom_vide = df["nom"].isna() | df["nom"].isin(["", "nan", "None"])
    if masque_nom_vide.sum() > 0:
        avertissements.append(
            str(int(masque_nom_vide.sum()))
            + " ligne(s) sans nom de joueuse supprimee(s)."
        )
        df = df[~masque_nom_vide]

    # Lignes strictement identiques : probable erreur de copier-coller
    # (elles doubleraient la charge). Conservees mais signalees, car
    # deux seances identiques le meme jour restent possibles (tournoi).
    nb_doublons = int(df.duplicated().sum())
    if nb_doublons > 0:
        avertissements.append(
            str(nb_doublons)
            + " ligne(s) strictement identique(s) detectee(s) : "
            + "verifiez qu'il ne s'agit pas d'un doublon de saisie "
            + "(elles sont conservees et comptees dans la charge)."
        )

    # Doublons probables de noms (casse differente) : « Salma B. » et
    # « salma b. » creeraient deux joueuses fantomes
    cles_minuscules = df["nom"].str.lower()
    variantes_par_cle = df.groupby(cles_minuscules)["nom"].nunique()
    cles_problematiques = variantes_par_cle[variantes_par_cle > 1].index
    for cle in cles_problematiques:
        variantes = sorted(df.loc[cles_minuscules == cle, "nom"].unique())
        avertissements.append(
            "Nom ecrit de plusieurs facons : "
            + " / ".join(variantes)
            + " — harmonisez l'orthographe pour un suivi correct."
        )

    if len(df) == 0:
        erreurs.append("Aucune ligne exploitable apres nettoyage.")
        return None, erreurs, avertissements

    df = df.sort_values(["nom", "date"]).reset_index(drop=True)
    return df, erreurs, avertissements


# ============================================================
# MODULE BIEN-ETRE QUOTIDIEN (questionnaire de Hooper)
# ------------------------------------------------------------
# Chaque matin, chaque joueuse note 4 items de 1 (tres bien)
# a 7 (tres mauvais) : sommeil, fatigue, courbatures, stress.
# Indice de Hooper = somme des 4 (de 4 a 28, plus bas = mieux).
# ============================================================

COLONNES_BIEN_ETRE = ["date", "nom", "sommeil", "fatigue", "courbatures", "stress"]
ITEMS_HOOPER = ["sommeil", "fatigue", "courbatures", "stress"]


def generer_demo_bien_etre():
    """Reponses quotidiennes de demonstration, correlees a la charge :
    les semaines dures degradent les scores, et la Joueuse 5 se
    deteriore nettement sur la derniere semaine (comme sa charge)."""
    graine = np.random.default_rng(23)

    noms = [
        "Joueuse 1", "Joueuse 2", "Joueuse 3", "Joueuse 4",
        "Joueuse 5", "Joueuse 6", "Joueuse 7", "Joueuse 8",
    ]

    date_debut = pd.Timestamp("2026-03-02")
    nb_semaines = 16
    lignes = []

    for i in range(len(noms)):
        # Niveau de base individuel (certaines dorment mieux que d'autres)
        base_individuelle = graine.uniform(1.8, 2.8)

        for semaine in range(nb_semaines):
            est_decharge = (semaine + 1) % 4 == 0 and semaine != nb_semaines - 1
            if est_decharge:
                effet_charge = -0.3
            else:
                effet_charge = 0.2 + 0.04 * (semaine % 4)

            # Deterioration marquee de la Joueuse 5 en fin de saison
            if i == 4 and semaine == nb_semaines - 1:
                effet_charge = 3.2

            for jour in range(7):
                date_reponse = date_debut + pd.Timedelta(days=semaine * 7 + jour)

                ligne = {"date": date_reponse, "nom": noms[i]}
                for item in ITEMS_HOOPER:
                    valeur = graine.normal(base_individuelle + effet_charge, 0.7)
                    ligne[item] = int(np.clip(round(valeur), 1, 7))
                lignes.append(ligne)

    df = pd.DataFrame(lignes)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["nom", "date"]).reset_index(drop=True)


def generer_modele_bien_etre():
    """Modele CSV du questionnaire quotidien avec 2 lignes d'exemple."""
    exemples = [
        {"date": "2026-09-08", "nom": "Salma B.", "sommeil": 2,
         "fatigue": 3, "courbatures": 2, "stress": 2},
        {"date": "2026-09-08", "nom": "Aya K.", "sommeil": 4,
         "fatigue": 5, "courbatures": 3, "stress": 3},
    ]
    df = pd.DataFrame(exemples, columns=COLONNES_BIEN_ETRE)
    tampon = io.StringIO()
    df.to_csv(tampon, index=False)
    return tampon.getvalue()


def valider_csv_bien_etre(fichier):
    """Valide le CSV bien-etre. Retourne (df, erreurs, avertissements)."""
    erreurs = []
    avertissements = []

    try:
        df = pd.read_csv(fichier)
    except Exception as probleme:
        erreurs.append("Fichier bien-etre illisible : " + str(probleme))
        return None, erreurs, avertissements

    nouvelles_colonnes = []
    for colonne in df.columns:
        nouvelles_colonnes.append(str(colonne).strip().lower())
    df.columns = nouvelles_colonnes

    for colonne in COLONNES_BIEN_ETRE:
        if colonne not in df.columns:
            erreurs.append("Bien-etre : colonne manquante « " + colonne + " »")
    if len(erreurs) > 0:
        return None, erreurs, avertissements

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    for item in ITEMS_HOOPER:
        df[item] = pd.to_numeric(df[item], errors="coerce")
        masque_bornes = df[item].notna() & ((df[item] < 1) | (df[item] > 7))
        if masque_bornes.sum() > 0:
            avertissements.append(
                "Bien-etre : " + str(int(masque_bornes.sum()))
                + " valeur(s) de « " + item
                + " » hors echelle 1-7 : exclue(s)."
            )
            df.loc[masque_bornes, item] = np.nan
    df["nom"] = df["nom"].astype(str).str.strip()
    df = df.dropna(subset=ITEMS_HOOPER)

    if len(df) == 0:
        erreurs.append("Bien-etre : aucune ligne exploitable.")
        return None, erreurs, avertissements

    return df.sort_values(["nom", "date"]).reset_index(drop=True), erreurs, avertissements


# ============================================================
# MODULE ANTHROPOMETRIE (croissance et maturation)
# ------------------------------------------------------------
# Mesures mensuelles de taille et de masse. La vitesse de
# croissance (cm/an) permet de reperer les pics de croissance,
# periodes de vulnerabilite chez les jeunes (Lloyd & Oliver).
# ============================================================

COLONNES_ANTHROPO = ["date", "nom", "taille_cm", "masse_kg"]


def generer_demo_anthropometrie():
    """Mesures mensuelles de demonstration. La Joueuse 3 est en
    pic de croissance (environ +8 cm/an)."""
    graine = np.random.default_rng(31)

    noms = [
        "Joueuse 1", "Joueuse 2", "Joueuse 3", "Joueuse 4",
        "Joueuse 5", "Joueuse 6", "Joueuse 7", "Joueuse 8",
    ]
    tailles_depart = [168.0, 176.0, 171.0, 163.0, 178.0, 174.0, 180.0, 166.0]
    masses_depart = [58.0, 65.0, 60.0, 55.0, 67.0, 63.0, 68.0, 57.0]

    dates_mesures = [
        pd.Timestamp("2026-03-05"), pd.Timestamp("2026-04-05"),
        pd.Timestamp("2026-05-05"), pd.Timestamp("2026-06-05"),
    ]

    lignes = []
    for i in range(len(noms)):
        # Croissance annuelle normale : 1 a 3 cm/an a cet age.
        # La Joueuse 3 est en plein pic : environ 8 cm/an.
        if i == 2:
            croissance_an = 8.0
        else:
            croissance_an = graine.uniform(1.0, 3.0)

        for m in range(len(dates_mesures)):
            jours_ecoules = (dates_mesures[m] - dates_mesures[0]).days
            taille = tailles_depart[i] + croissance_an * jours_ecoules / 365.0
            taille = taille + graine.normal(0, 0.06)
            masse = masses_depart[i] + 0.4 * m + graine.normal(0, 0.3)

            lignes.append({
                "date": dates_mesures[m],
                "nom": noms[i],
                "taille_cm": round(float(taille), 1),
                "masse_kg": round(float(masse), 1),
            })

    df = pd.DataFrame(lignes)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["nom", "date"]).reset_index(drop=True)


def generer_modele_anthropometrie():
    """Modele CSV des mesures anthropometriques."""
    exemples = [
        {"date": "2026-09-05", "nom": "Salma B.", "taille_cm": 172.5, "masse_kg": 61.0},
        {"date": "2026-10-05", "nom": "Salma B.", "taille_cm": 173.0, "masse_kg": 61.4},
    ]
    df = pd.DataFrame(exemples, columns=COLONNES_ANTHROPO)
    tampon = io.StringIO()
    df.to_csv(tampon, index=False)
    return tampon.getvalue()


def valider_csv_anthropometrie(fichier):
    """Valide le CSV anthropometrie."""
    erreurs = []
    avertissements = []

    try:
        df = pd.read_csv(fichier)
    except Exception as probleme:
        erreurs.append("Anthropometrie : fichier illisible : " + str(probleme))
        return None, erreurs, avertissements

    nouvelles_colonnes = []
    for colonne in df.columns:
        nouvelles_colonnes.append(str(colonne).strip().lower())
    df.columns = nouvelles_colonnes

    for colonne in COLONNES_ANTHROPO:
        if colonne not in df.columns:
            erreurs.append("Anthropometrie : colonne manquante « " + colonne + " »")
    if len(erreurs) > 0:
        return None, erreurs, avertissements

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["taille_cm"] = pd.to_numeric(df["taille_cm"], errors="coerce")
    df["masse_kg"] = pd.to_numeric(df["masse_kg"], errors="coerce")
    df["nom"] = df["nom"].astype(str).str.strip()
    df = df.dropna(subset=["taille_cm"])

    if len(df) == 0:
        erreurs.append("Anthropometrie : aucune ligne exploitable.")
        return None, erreurs, avertissements

    return df.sort_values(["nom", "date"]).reset_index(drop=True), erreurs, avertissements


# ============================================================
# MODULE JOURNAL DES BLESSURES
# ------------------------------------------------------------
# Une ligne par episode : blessure ou maladie, zone touchee,
# nombre de jours d'absence. Permet de calculer la
# disponibilite et de croiser les alertes avec les faits.
# ============================================================

COLONNES_BLESSURES = ["date_debut", "nom", "type", "zone", "jours_absence"]


def generer_demo_blessures():
    """Journal de demonstration : 3 episodes sur la saison."""
    lignes = [
        {"date_debut": pd.Timestamp("2026-04-10"), "nom": "Joueuse 7",
         "type": "Blessure", "zone": "Cheville (entorse)", "jours_absence": 12},
        {"date_debut": pd.Timestamp("2026-05-15"), "nom": "Joueuse 2",
         "type": "Blessure", "zone": "Genou (douleur tendineuse)", "jours_absence": 5},
        {"date_debut": pd.Timestamp("2026-05-28"), "nom": "Joueuse 8",
         "type": "Maladie", "zone": "—", "jours_absence": 3},
    ]
    df = pd.DataFrame(lignes)
    df["date_debut"] = pd.to_datetime(df["date_debut"])
    return df


def generer_modele_blessures():
    """Modele CSV du journal des blessures."""
    exemples = [
        {"date_debut": "2026-10-12", "nom": "Salma B.", "type": "Blessure",
         "zone": "Cheville (entorse)", "jours_absence": 10},
        {"date_debut": "2026-11-03", "nom": "Aya K.", "type": "Maladie",
         "zone": "—", "jours_absence": 3},
    ]
    df = pd.DataFrame(exemples, columns=COLONNES_BLESSURES)
    tampon = io.StringIO()
    df.to_csv(tampon, index=False)
    return tampon.getvalue()


def valider_csv_blessures(fichier):
    """Valide le CSV du journal des blessures."""
    erreurs = []
    avertissements = []

    try:
        df = pd.read_csv(fichier)
    except Exception as probleme:
        erreurs.append("Blessures : fichier illisible : " + str(probleme))
        return None, erreurs, avertissements

    nouvelles_colonnes = []
    for colonne in df.columns:
        nouvelles_colonnes.append(str(colonne).strip().lower())
    df.columns = nouvelles_colonnes

    for colonne in COLONNES_BLESSURES:
        if colonne not in df.columns:
            erreurs.append("Blessures : colonne manquante « " + colonne + " »")
    if len(erreurs) > 0:
        return None, erreurs, avertissements

    df["date_debut"] = pd.to_datetime(df["date_debut"], errors="coerce")
    df = df.dropna(subset=["date_debut"])
    df["jours_absence"] = pd.to_numeric(df["jours_absence"], errors="coerce").fillna(0)
    df["nom"] = df["nom"].astype(str).str.strip()
    df["type"] = df["type"].astype(str).str.strip()
    df["zone"] = df["zone"].astype(str).str.strip()

    return df.sort_values("date_debut").reset_index(drop=True), erreurs, avertissements


# ============================================================
# VALIDATION D'UNE SAISIE RAPIDE DE TESTS
# ------------------------------------------------------------
# Sprint 2 (roadmap securite §16-17) : l'entraineur saisit un
# test pour toute l'equipe d'un coup. La validation est ATOMIQUE
# — on verifie toutes les lignes AVANT tout ajout, et si une
# seule valeur est invalide, rien n'est integre (pas de fusion
# partielle).
# ============================================================

def valider_saisie_tests(lignes, colonne_test):
    """Valide un lot de saisies de tests pour une seule colonne.

    `lignes` : liste de dictionnaires {nom, poste, valeur} ou
    valeur peut etre None/vide (joueuse non testee, ignoree).
    `colonne_test` : cle parmi COLONNES_TESTS.

    Retourne (lignes_valides, erreurs).
      lignes_valides : liste prete pour DepotSession.ajouter_mesures_tests
      erreurs        : liste de messages ; si non vide, NE RIEN ajouter.

    Bornes de plausibilite par test (rejet des valeurs impossibles) :
    """
    erreurs = []
    valides = []

    # Bornes larges de plausibilite (au-dela = erreur de saisie)
    bornes = {
        "cmj_cm": (10.0, 80.0),
        "detente_attaque_cm": (180.0, 380.0),
        "detente_contre_cm": (170.0, 360.0),
        "vitesse_10m_s": (1.2, 3.5),
        "t_test_s": (7.0, 18.0),
        "medecine_ball_cm": (200.0, 1200.0),
        "navette_s": (7.0, 20.0),
    }

    if colonne_test not in COLONNES_TESTS:
        return [], ["Test inconnu : " + str(colonne_test)]

    mini, maxi = bornes.get(colonne_test, (None, None))

    for ligne in lignes:
        brut = ligne.get("valeur", None)
        # Cellule vide = joueuse non testee ce jour : on ignore sans erreur
        if brut is None or str(brut).strip() == "":
            continue
        try:
            valeur = float(str(brut).replace(",", "."))
        except (TypeError, ValueError):
            erreurs.append(
                ligne.get("nom", "?") + " : « " + str(brut)
                + " » n'est pas un nombre."
            )
            continue
        if mini is not None and (valeur < mini or valeur > maxi):
            erreurs.append(
                ligne.get("nom", "?") + " : " + str(valeur)
                + " hors des bornes plausibles ["
                + str(mini) + " ; " + str(maxi) + "] pour ce test."
            )
            continue
        valides.append({
            "nom": ligne.get("nom"),
            "poste": ligne.get("poste", ""),
            colonne_test: valeur,
        })

    return valides, erreurs
