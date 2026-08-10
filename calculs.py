# ============================================================
# calculs.py — Calculs scientifiques du dashboard FUS-VB
# ------------------------------------------------------------
# Methode de charge : seance-RPE (Foster, 2001)
#     charge d'une seance = RPE (1-10) x duree (minutes)
#
# Ratio ACWR (Acute:Chronic Workload Ratio) :
#     charge aigue    = somme glissante sur 7 jours
#     charge chronique = moyenne des charges hebdomadaires
#                        sur 28 jours (= somme 28 jours / 4)
#     ACWR = aigue / chronique
#
# Zones d'interpretation (litterature : Gabbett, Impellizzeri) :
#     < 0.80        sous-charge (desentrainement possible)
#     0.80 - 1.30   zone optimale
#     1.30 - 1.50   vigilance
#     > 1.50        risque eleve de blessure
# ============================================================

import numpy as np
import pandas as pd

from donnees import COLONNES_TESTS, SENS_AMELIORATION


# ------------------------------------------------------------
# 1. CHARGE D'ENTRAINEMENT QUOTIDIENNE
# ------------------------------------------------------------

def calculer_charges_quotidiennes(df):
    """Retourne un DataFrame : une ligne par joueuse et par jour,
    avec la charge totale du jour (RPE x duree, sommee si 2 seances)."""
    donnees_valides = df.dropna(subset=["rpe", "duree_min"]).copy()
    donnees_valides["charge"] = donnees_valides["rpe"] * donnees_valides["duree_min"]

    charges = donnees_valides.groupby(["nom", "date"], as_index=False)["charge"].sum()
    charges = charges.sort_values(["nom", "date"]).reset_index(drop=True)
    return charges


# ------------------------------------------------------------
# 2. ACWR PAR JOUEUSE
# ------------------------------------------------------------

def calculer_acwr_joueuse(charges_joueuse):
    """Calcule l'ACWR jour par jour pour UNE joueuse.

    Entree : DataFrame avec colonnes date + charge (une joueuse).
    Sortie : DataFrame avec date, charge_aigue, charge_chronique, acwr.
    """
    if len(charges_joueuse) == 0:
        return pd.DataFrame(
            columns=["date", "charge_aigue", "charge_chronique", "acwr"]
        )

    # Construire un calendrier continu (jours sans seance = charge 0)
    serie = charges_joueuse.set_index("date")["charge"]
    calendrier = pd.date_range(serie.index.min(), serie.index.max(), freq="D")
    serie = serie.reindex(calendrier, fill_value=0.0)

    # Charge aigue : somme glissante 7 jours
    aigue = serie.rolling(window=7, min_periods=7).sum()

    # Charge chronique : somme glissante 28 jours divisee par 4
    chronique = serie.rolling(window=28, min_periods=28).sum() / 4.0

    resultat = pd.DataFrame({
        "date": calendrier,
        "charge_aigue": aigue.values,
        "charge_chronique": chronique.values,
    })

    # ACWR seulement quand la charge chronique existe et n'est pas nulle
    acwr_valeurs = []
    for indice in range(len(resultat)):
        chronique_jour = resultat.loc[indice, "charge_chronique"]
        aigue_jour = resultat.loc[indice, "charge_aigue"]
        if pd.isna(chronique_jour) or chronique_jour <= 0:
            acwr_valeurs.append(np.nan)
        else:
            acwr_valeurs.append(aigue_jour / chronique_jour)
    resultat["acwr"] = acwr_valeurs

    return resultat


def calculer_acwr_equipe(df):
    """Calcule l'ACWR pour toutes les joueuses.
    Retourne un DataFrame avec colonnes : nom, date, charge_aigue,
    charge_chronique, acwr."""
    charges = calculer_charges_quotidiennes(df)

    morceaux = []
    for nom in charges["nom"].unique():
        charges_joueuse = charges[charges["nom"] == nom]
        acwr_joueuse = calculer_acwr_joueuse(charges_joueuse)
        acwr_joueuse.insert(0, "nom", nom)
        morceaux.append(acwr_joueuse)

    if len(morceaux) == 0:
        return pd.DataFrame(
            columns=["nom", "date", "charge_aigue", "charge_chronique", "acwr"]
        )
    return pd.concat(morceaux, ignore_index=True)


# ------------------------------------------------------------
# 3. INTERPRETATION DE L'ACWR
# ------------------------------------------------------------

def interpreter_acwr(valeur):
    """Retourne (etiquette, couleur, emoji) pour une valeur d'ACWR.

    Vocabulaire volontairement descriptif : l'ACWR est un signal de
    vigilance sur la variation de charge, pas un predicteur individuel
    de blessure valide (Impellizzeri et al., 2020)."""
    if valeur is None or (isinstance(valeur, float) and np.isnan(valeur)):
        return ("Donnees insuffisantes", "#9AA0A6", "⏳")
    if valeur < 0.80:
        return ("Charge en baisse marquee", "#4A90D9", "🔵")
    if valeur <= 1.30:
        return ("Zone habituelle", "#2E9E5B", "🟢")
    if valeur <= 1.50:
        return ("Vigilance", "#E8A13C", "🟠")
    return ("Hausse forte — vigilance accrue", "#D64545", "🔴")


def cle_acwr(valeur):
    """Retourne (cle_etiquette, couleur, emoji) — la cle sert a la
    traduction (i18n.etiquette_acwr). Meme classification que
    interpreter_acwr, mais renvoie une cle stable plutot qu'un
    libelle francais fige."""
    if valeur is None or (isinstance(valeur, float) and np.isnan(valeur)):
        return ("insuffisant", "#9AA0A6", "⏳")
    if valeur < 0.80:
        return ("baisse", "#4A90D9", "🔵")
    if valeur <= 1.30:
        return ("habituelle", "#2E9E5B", "🟢")
    if valeur <= 1.50:
        return ("vigilance", "#E8A13C", "🟠")
    return ("hausse", "#D64545", "🔴")


def dernier_acwr_par_joueuse(acwr_equipe):
    """Retourne un DataFrame : derniere valeur d'ACWR connue par joueuse."""
    lignes = []
    for nom in acwr_equipe["nom"].unique():
        donnees_joueuse = acwr_equipe[acwr_equipe["nom"] == nom]
        donnees_valides = donnees_joueuse.dropna(subset=["acwr"])
        if len(donnees_valides) == 0:
            lignes.append({"nom": nom, "date": None, "acwr": np.nan})
        else:
            derniere = donnees_valides.iloc[-1]
            lignes.append({
                "nom": nom,
                "date": derniere["date"],
                "acwr": derniere["acwr"],
            })
    return pd.DataFrame(lignes)


# ------------------------------------------------------------
# 4. PROGRESSION SUR LES TESTS PHYSIQUES
# ------------------------------------------------------------

def extraire_tests(df, nom):
    """Retourne uniquement les lignes de tests (au moins une valeur)
    pour une joueuse, triees par date."""
    donnees_joueuse = df[df["nom"] == nom].copy()
    masque_test = donnees_joueuse[COLONNES_TESTS].notna().any(axis=1)
    tests = donnees_joueuse[masque_test].sort_values("date")
    return tests


def calculer_progression(df, nom):
    """Compare le premier et le dernier test de chaque indicateur.

    Retourne un dictionnaire :
        indicateur -> {premier, dernier, delta, delta_pct, en_progres}
    """
    tests = extraire_tests(df, nom)
    resultat = {}

    for colonne in COLONNES_TESTS:
        valeurs = tests.dropna(subset=[colonne])
        if len(valeurs) < 2:
            continue

        premier = float(valeurs[colonne].iloc[0])
        dernier = float(valeurs[colonne].iloc[-1])
        delta = dernier - premier

        if premier != 0:
            delta_pct = delta / premier * 100.0
        else:
            delta_pct = 0.0

        plus_haut_est_mieux = SENS_AMELIORATION[colonne]
        if plus_haut_est_mieux:
            en_progres = delta > 0
        else:
            en_progres = delta < 0

        resultat[colonne] = {
            "premier": premier,
            "dernier": dernier,
            "delta": delta,
            "delta_pct": delta_pct,
            "en_progres": en_progres,
        }

    return resultat


# ------------------------------------------------------------
# 5. SYNTHESE EQUIPE (tableau de la vue d'ensemble)
# ------------------------------------------------------------

def construire_synthese_equipe(df):
    """Construit le tableau de synthese : une ligne par joueuse avec
    poste, dernier CMJ, derniere vitesse, ACWR actuel et statut."""
    acwr_equipe = calculer_acwr_equipe(df)
    derniers_acwr = dernier_acwr_par_joueuse(acwr_equipe)

    lignes = []
    for nom in sorted(df["nom"].unique()):
        donnees_joueuse = df[df["nom"] == nom]
        poste = donnees_joueuse["poste"].iloc[-1]

        tests = extraire_tests(df, nom)

        dernier_cmj = np.nan
        cmj_valides = tests.dropna(subset=["cmj_cm"])
        if len(cmj_valides) > 0:
            dernier_cmj = float(cmj_valides["cmj_cm"].iloc[-1])

        derniere_vitesse = np.nan
        vitesses_valides = tests.dropna(subset=["vitesse_10m_s"])
        if len(vitesses_valides) > 0:
            derniere_vitesse = float(vitesses_valides["vitesse_10m_s"].iloc[-1])

        derniere_attaque = np.nan
        attaques_valides = tests.dropna(subset=["detente_attaque_cm"])
        if len(attaques_valides) > 0:
            derniere_attaque = float(attaques_valides["detente_attaque_cm"].iloc[-1])

        acwr_valeur = np.nan
        ligne_acwr = derniers_acwr[derniers_acwr["nom"] == nom]
        if len(ligne_acwr) > 0:
            acwr_valeur = float(ligne_acwr["acwr"].iloc[0])

        etiquette, couleur, emoji = interpreter_acwr(acwr_valeur)

        lignes.append({
            "Joueuse": nom,
            "Poste": poste,
            "CMJ (cm)": dernier_cmj,
            "Attaque (cm)": derniere_attaque,
            "Sprint 10 m (s)": derniere_vitesse,
            "ACWR": acwr_valeur,
            "Statut": emoji + " " + etiquette,
        })

    return pd.DataFrame(lignes), acwr_equipe


# ============================================================
# 6. BIEN-ETRE : INDICE DE HOOPER
# ============================================================

def calculer_hooper(df_bien_etre):
    """Ajoute la colonne hooper (somme des 4 items, de 4 a 28)."""
    df = df_bien_etre.copy()
    df["hooper"] = (
        df["sommeil"] + df["fatigue"] + df["courbatures"] + df["stress"]
    )
    return df


def interpreter_hooper(valeur):
    """Retourne (etiquette, emoji) pour un indice de Hooper.
    Seuils indicatifs : les alertes individualisees (Z-scores)
    restent la reference."""
    if valeur is None or (isinstance(valeur, float) and np.isnan(valeur)):
        return ("Pas de reponse", "⏳")
    if valeur <= 13:
        return ("Bon etat", "🟢")
    if valeur <= 19:
        return ("Etat moyen", "🟠")
    return ("Etat degrade", "🔴")


def bien_etre_du_jour(df_bien_etre):
    """Retourne les dernieres reponses de chaque joueuse
    (matrice du jour pour l'entraineur)."""
    df = calculer_hooper(df_bien_etre)
    lignes = []
    for nom in sorted(df["nom"].unique()):
        donnees_joueuse = df[df["nom"] == nom].sort_values("date")
        derniere = donnees_joueuse.iloc[-1]
        etiquette, emoji = interpreter_hooper(float(derniere["hooper"]))
        lignes.append({
            "Joueuse": nom,
            "Date": derniere["date"].strftime("%d/%m"),
            "Sommeil": int(derniere["sommeil"]),
            "Fatigue": int(derniere["fatigue"]),
            "Courbatures": int(derniere["courbatures"]),
            "Stress": int(derniere["stress"]),
            "Hooper": int(derniere["hooper"]),
            "Etat": emoji + " " + etiquette,
        })
    return pd.DataFrame(lignes)


# ============================================================
# 7. MONOTONIE ET CONTRAINTE (Foster)
# ------------------------------------------------------------
# Monotonie = moyenne des charges quotidiennes / ecart-type
#             (fenetre de 7 jours, jours de repos inclus)
# Contrainte = charge hebdomadaire x monotonie
# Une monotonie > 2 signale un entrainement trop uniforme.
# ============================================================

def calculer_monotonie_contrainte(df):
    """Retourne un DataFrame : nom, date, monotonie, contrainte
    (valeurs glissantes sur 7 jours)."""
    charges = calculer_charges_quotidiennes(df)
    morceaux = []

    for nom in charges["nom"].unique():
        charges_joueuse = charges[charges["nom"] == nom]
        serie = charges_joueuse.set_index("date")["charge"]
        calendrier = pd.date_range(serie.index.min(), serie.index.max(), freq="D")
        serie = serie.reindex(calendrier, fill_value=0.0)

        moyenne = serie.rolling(window=7, min_periods=7).mean()
        ecart_type = serie.rolling(window=7, min_periods=7).std()
        charge_hebdo = serie.rolling(window=7, min_periods=7).sum()

        monotonie_valeurs = []
        for indice in range(len(calendrier)):
            m = moyenne.iloc[indice]
            e = ecart_type.iloc[indice]
            if pd.isna(m) or pd.isna(e) or e == 0:
                monotonie_valeurs.append(np.nan)
            else:
                monotonie_valeurs.append(m / e)

        resultat = pd.DataFrame({
            "nom": nom,
            "date": calendrier,
            "monotonie": monotonie_valeurs,
            "charge_hebdo": charge_hebdo.values,
        })
        resultat["contrainte"] = resultat["monotonie"] * resultat["charge_hebdo"]
        morceaux.append(resultat)

    if len(morceaux) == 0:
        return pd.DataFrame(columns=["nom", "date", "monotonie", "charge_hebdo", "contrainte"])
    return pd.concat(morceaux, ignore_index=True)


# ============================================================
# 8. CHARGE DE SAUTS
# ============================================================

def calculer_sauts_hebdo(df):
    """Somme hebdomadaire des sauts par joueuse.
    Retourne un DataFrame : nom, semaine, sauts."""
    if "sauts" not in df.columns:
        return pd.DataFrame(columns=["nom", "semaine", "sauts"])

    donnees = df.dropna(subset=["sauts"]).copy()
    if len(donnees) == 0:
        return pd.DataFrame(columns=["nom", "semaine", "sauts"])

    donnees["semaine"] = donnees["date"].dt.to_period("W").dt.start_time
    resultat = donnees.groupby(["nom", "semaine"], as_index=False)["sauts"].sum()
    return resultat.sort_values(["nom", "semaine"]).reset_index(drop=True)


# ============================================================
# 9. CROISSANCE (vitesse en cm/an)
# ------------------------------------------------------------
# Vitesse estimee entre deux mesures consecutives :
#     (taille2 - taille1) / jours x 365
# Au-dela d'environ 7 cm/an : pic de croissance probable,
# periode de vigilance accrue (charge, technique, souplesse).
# ============================================================

def calculer_croissance(df_anthro):
    """Retourne un DataFrame : nom, date, taille_cm, masse_kg,
    vitesse_cm_an (NaN pour la premiere mesure de chaque joueuse)."""
    morceaux = []
    for nom in df_anthro["nom"].unique():
        mesures = df_anthro[df_anthro["nom"] == nom].sort_values("date").copy()

        vitesses = [np.nan]
        for indice in range(1, len(mesures)):
            date_actuelle = mesures["date"].iloc[indice]

            # Mesure de reference : la plus recente datant d'au moins
            # 60 jours, pour lisser le bruit de mesure (une erreur de
            # 2 mm sur 1 mois fausse la vitesse de plus de 2 cm/an).
            indice_reference = indice - 1
            for candidat in range(indice - 1, -1, -1):
                ecart_jours = (date_actuelle - mesures["date"].iloc[candidat]).days
                indice_reference = candidat
                if ecart_jours >= 60:
                    break

            delta_cm = mesures["taille_cm"].iloc[indice] - mesures["taille_cm"].iloc[indice_reference]
            delta_jours = (date_actuelle - mesures["date"].iloc[indice_reference]).days
            if delta_jours <= 0:
                vitesses.append(np.nan)
            else:
                vitesses.append(delta_cm / delta_jours * 365.0)

        mesures["vitesse_cm_an"] = vitesses
        morceaux.append(mesures)

    if len(morceaux) == 0:
        return df_anthro.copy()
    return pd.concat(morceaux, ignore_index=True)


# ============================================================
# 10. DISPONIBILITE (journal des blessures)
# ============================================================

def _fusionner_intervalles(intervalles):
    """Fusionne une liste d'intervalles (debut, fin) qui se chevauchent
    et retourne le nombre total de jours uniques couverts.
    Exemple : [1-10 mars] + [5-15 mars] = 15 jours, pas 21."""
    if len(intervalles) == 0:
        return 0

    intervalles = sorted(intervalles)
    total_jours = 0
    debut_courant, fin_courant = intervalles[0]

    for debut_ep, fin_ep in intervalles[1:]:
        if debut_ep <= fin_courant:
            # Chevauchement : etendre l'intervalle courant
            fin_courant = max(fin_courant, fin_ep)
        else:
            total_jours = total_jours + (fin_courant - debut_courant).days + 1
            debut_courant, fin_courant = debut_ep, fin_ep

    total_jours = total_jours + (fin_courant - debut_courant).days + 1
    return total_jours


def calculer_disponibilite(df_blessures, df_seances):
    """Pour chaque joueuse : episodes, jours d'absence et
    disponibilite en % sur la periode des donnees de seances.

    Les episodes qui se chevauchent sont fusionnes avant le comptage
    (un meme jour n'est jamais compte deux fois) et chaque episode est
    recadre sur la periode couverte par les seances : les jours situes
    hors periode ne penalisent pas la disponibilite."""
    debut = df_seances["date"].min().normalize()
    fin = df_seances["date"].max().normalize()
    jours_periode = (fin - debut).days + 1

    lignes = []
    for nom in sorted(df_seances["nom"].unique()):
        episodes = df_blessures[df_blessures["nom"] == nom]
        nb_episodes = len(episodes)

        # Construire les intervalles [debut, fin] de chaque episode,
        # recadres sur la periode d'observation
        intervalles = []
        for indice in range(len(episodes)):
            duree = episodes["jours_absence"].iloc[indice]
            if pd.isna(duree) or int(duree) <= 0:
                continue
            debut_episode = episodes["date_debut"].iloc[indice].normalize()
            fin_episode = debut_episode + pd.Timedelta(days=int(duree) - 1)

            debut_recadre = max(debut_episode, debut)
            fin_recadree = min(fin_episode, fin)
            if debut_recadre <= fin_recadree:
                intervalles.append((debut_recadre, fin_recadree))

        jours_absence = _fusionner_intervalles(intervalles)
        disponibilite = (jours_periode - jours_absence) / jours_periode * 100.0

        lignes.append({
            "Joueuse": nom,
            "Episodes": nb_episodes,
            "Jours d'absence": int(jours_absence),
            "Disponibilite (%)": round(disponibilite, 1),
        })
    return pd.DataFrame(lignes)


# ============================================================
# 11. ALERTES INDIVIDUALISEES (Z-scores)
# ------------------------------------------------------------
# Principe : comparer chaque joueuse a SA PROPRE reference
# plutot qu'a des seuils fixes.
#     Z = (valeur du jour - moyenne de reference) / ecart-type
# Reference = les 28 jours precedant la valeur evaluee.
# ============================================================

def zscore_derniere_valeur(serie_dates, serie_valeurs):
    """Z-score de la derniere valeur par rapport aux 28 jours
    qui la precedent. Retourne (zscore, derniere_valeur) ou
    (None, None) si la reference est insuffisante."""
    if len(serie_valeurs) < 8:
        return None, None

    derniere_date = serie_dates.iloc[-1]
    derniere_valeur = float(serie_valeurs.iloc[-1])

    debut_reference = derniere_date - pd.Timedelta(days=28)
    masque = (serie_dates >= debut_reference) & (serie_dates < derniere_date)
    reference = serie_valeurs[masque]

    if len(reference) < 7:
        return None, None

    moyenne = float(reference.mean())
    ecart_type = float(reference.std())
    if ecart_type == 0:
        return None, None

    return (derniere_valeur - moyenne) / ecart_type, derniere_valeur


def zscore_vs_historique(serie_valeurs, minimum_reference=28):
    """Z-score de la derniere valeur par rapport a TOUT l'historique
    precedent. Adapte aux series periodisees ou une fenetre de 28 jours
    serait biaisee par le cycle charge/decharge."""
    if len(serie_valeurs) < minimum_reference + 1:
        return None, None
    derniere_valeur = float(serie_valeurs.iloc[-1])
    reference = serie_valeurs.iloc[:-1]
    moyenne = float(reference.mean())
    ecart_type = float(reference.std())
    if ecart_type == 0:
        return None, None
    return (derniere_valeur - moyenne) / ecart_type, derniere_valeur


def construire_alertes_individualisees(df_seances, df_bien_etre=None,
                                       df_anthro=None):
    """Passe en revue toutes les joueuses et retourne une liste
    de dictionnaires : {nom, module, message, niveau}.
    niveau : 'alerte' (rouge) ou 'attention' (orange)."""
    alertes = []

    # --- 1. Bien-etre : Hooper au-dessus de la reference perso ---
    if df_bien_etre is not None and len(df_bien_etre) > 0:
        df_h = calculer_hooper(df_bien_etre)
        for nom in df_h["nom"].unique():
            donnees_joueuse = df_h[df_h["nom"] == nom].sort_values("date")
            z, valeur = zscore_derniere_valeur(
                donnees_joueuse["date"], donnees_joueuse["hooper"]
            )
            if z is not None and z > 1.5:
                if z > 2.5:
                    niveau = "alerte"
                else:
                    niveau = "attention"
                alertes.append({
                    "nom": nom, "module": "Bien-etre", "niveau": niveau,
                    "cle": "bien_etre",
                    "params": {"valeur": int(valeur), "z": round(z, 1)},
                    "message": "Indice de Hooper a " + str(int(valeur))
                               + " (Z = +" + str(round(z, 1))
                               + " vs sa reference 28 j) : etat degrade.",
                })

    # --- 2. Monotonie superieure a 2 -----------------------------
    monotonie = calculer_monotonie_contrainte(df_seances)
    for nom in monotonie["nom"].unique():
        donnees_joueuse = monotonie[monotonie["nom"] == nom].dropna(subset=["monotonie"])
        if len(donnees_joueuse) == 0:
            continue
        derniere = float(donnees_joueuse["monotonie"].iloc[-1])
        if derniere > 2.0:
            alertes.append({
                "nom": nom, "module": "Monotonie", "niveau": "attention",
                "cle": "monotonie",
                "params": {"valeur": round(derniere, 1)},
                "message": "Monotonie a " + str(round(derniere, 1))
                           + " (> 2) : entrainement trop uniforme, varier les charges.",
            })

    # --- 3. Contrainte au-dessus de la reference perso -----------
    for nom in monotonie["nom"].unique():
        donnees_joueuse = monotonie[monotonie["nom"] == nom].dropna(subset=["contrainte"])
        z, valeur = zscore_vs_historique(donnees_joueuse["contrainte"])
        if z is not None and z > 2.0:
            if z > 3.0:
                niveau = "alerte"
            else:
                niveau = "attention"
            alertes.append({
                "nom": nom, "module": "Contrainte", "niveau": niveau,
                "cle": "contrainte",
                "params": {"z": round(z, 1)},
                "message": "Contrainte hebdomadaire inhabituellement elevee "
                           + "(Z = +" + str(round(z, 1)) + " vs sa reference 28 j).",
            })

    # --- 4. Pic de sauts vs moyenne personnelle ------------------
    sauts = calculer_sauts_hebdo(df_seances)
    for nom in sauts["nom"].unique():
        donnees_joueuse = sauts[sauts["nom"] == nom]
        if len(donnees_joueuse) < 5:
            continue
        derniere_semaine = float(donnees_joueuse["sauts"].iloc[-1])
        reference = donnees_joueuse["sauts"].iloc[-5:-1]
        moyenne_reference = float(reference.mean())
        if moyenne_reference > 0 and derniere_semaine > 1.5 * moyenne_reference:
            alertes.append({
                "nom": nom, "module": "Sauts", "niveau": "attention",
                "cle": "sauts",
                "params": {"valeur": int(derniere_semaine),
                           "moyenne": int(moyenne_reference)},
                "message": "Volume de sauts a " + str(int(derniere_semaine))
                           + " cette semaine (moyenne 4 sem. : "
                           + str(int(moyenne_reference))
                           + ") : surveiller les genoux.",
            })

    # --- 5. Chute du CMJ sous la reference perso -----------------
    for nom in df_seances["nom"].unique():
        tests = extraire_tests(df_seances, nom).dropna(subset=["cmj_cm"])
        if len(tests) < 4:
            continue
        dernier = float(tests["cmj_cm"].iloc[-1])
        reference = tests["cmj_cm"].iloc[:-1]
        moyenne = float(reference.mean())
        ecart_type = float(reference.std())
        if ecart_type == 0:
            continue
        z = (dernier - moyenne) / ecart_type
        if z < -1.0:
            alertes.append({
                "nom": nom, "module": "CMJ", "niveau": "attention",
                "cle": "cmj",
                "params": {"valeur": round(dernier, 1), "z": round(z, 1)},
                "message": "CMJ a " + str(round(dernier, 1))
                           + " cm, en dessous de sa reference (Z = "
                           + str(round(z, 1)) + ") : fatigue neuromusculaire possible.",
            })

    # --- 6. Pic de croissance ------------------------------------
    if df_anthro is not None and len(df_anthro) > 0:
        croissance = calculer_croissance(df_anthro)
        for nom in croissance["nom"].unique():
            donnees_joueuse = croissance[croissance["nom"] == nom].dropna(subset=["vitesse_cm_an"])
            if len(donnees_joueuse) == 0:
                continue
            derniere_vitesse = float(donnees_joueuse["vitesse_cm_an"].iloc[-1])
            if derniere_vitesse > 7.0:
                alertes.append({
                    "nom": nom, "module": "Croissance", "niveau": "attention",
                    "cle": "croissance",
                    "params": {"valeur": round(derniere_vitesse, 1)},
                    "message": "Vitesse de croissance estimee a "
                               + str(round(derniere_vitesse, 1))
                               + " cm/an : pic de croissance probable, "
                               + "moduler charge et sauts.",
                })

    return alertes


# ============================================================
# 12. CENTRE D'ALERTES COMPLET
# ------------------------------------------------------------
# Fusionne les alertes ACWR (seuils descriptifs) et les alertes
# individualisees (Z-scores). La construction vit ici, pas dans
# l'interface : la vue d'equipe ET la fiche joueuse reutilisent
# la meme liste.
# ============================================================

def construire_toutes_alertes(df_seances, df_bien_etre=None, df_anthro=None):
    """Retourne la liste complete des alertes, rouges d'abord.
    Chaque alerte : {nom, module, niveau, message}."""
    synthese, acwr_equipe = construire_synthese_equipe(df_seances)

    alertes = []
    for indice in range(len(synthese)):
        ligne = synthese.iloc[indice]
        valeur = ligne["ACWR"]
        if pd.notna(valeur) and (valeur > 1.30 or valeur < 0.80):
            if valeur > 1.50:
                niveau = "alerte"
            else:
                niveau = "attention"
            etiquette, couleur, emoji = interpreter_acwr(float(valeur))
            cle_etiq, _, _ = cle_acwr(float(valeur))
            alertes.append({
                "nom": str(ligne["Joueuse"]), "module": "ACWR",
                "niveau": niveau,
                "cle": "acwr",
                "params": {"valeur": round(float(valeur), 2),
                           "cle_etiquette": cle_etiq},
                "message": "ACWR a " + str(round(float(valeur), 2))
                           + " : " + etiquette + ".",
            })

    alertes = alertes + construire_alertes_individualisees(
        df_seances, df_bien_etre, df_anthro
    )

    rouges = []
    oranges = []
    for alerte in alertes:
        if alerte["niveau"] == "alerte":
            rouges.append(alerte)
        else:
            oranges.append(alerte)
    return rouges + oranges
