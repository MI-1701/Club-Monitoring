# ============================================================
# tests/test_calculs.py — Tests des calculs scientifiques
# ------------------------------------------------------------
# Chaque indicateur est verifie sur un cas synthetique dont le
# resultat attendu est calculable a la main. Lancer : pytest -q
# ============================================================

import numpy as np
import pandas as pd
import pytest

from calculs import (
    _fusionner_intervalles,
    calculer_acwr_equipe,
    calculer_charges_quotidiennes,
    calculer_croissance,
    calculer_disponibilite,
    calculer_hooper,
    calculer_monotonie_contrainte,
    construire_alertes_individualisees,
    interpreter_acwr,
    interpreter_hooper,
    zscore_derniere_valeur,
    zscore_vs_historique,
)
from donnees import generer_donnees_demo


# ------------------------------------------------------------
# Outils de construction de donnees synthetiques
# ------------------------------------------------------------

def construire_seances(charges_par_jour, nom="Test", poste="Attaquante"):
    """Construit un DataFrame de seances : une seance par jour,
    duree 10 min, RPE = charge / 10 (donc charge = valeur donnee)."""
    date_debut = pd.Timestamp("2026-01-01")
    lignes = []
    for indice, charge in enumerate(charges_par_jour):
        lignes.append({
            "date": date_debut + pd.Timedelta(days=indice),
            "nom": nom, "poste": poste,
            "rpe": charge / 10.0, "duree_min": 10.0,
            "sauts": np.nan,
        })
    df = pd.DataFrame(lignes)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ------------------------------------------------------------
# 1. Charge quotidienne (seance-RPE)
# ------------------------------------------------------------

def test_charge_deux_seances_meme_jour_sont_sommees():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-01"]),
        "nom": ["A", "A"], "poste": ["P", "P"],
        "rpe": [6, 4], "duree_min": [60, 30],
    })
    charges = calculer_charges_quotidiennes(df)
    assert len(charges) == 1
    assert charges["charge"].iloc[0] == 6 * 60 + 4 * 30  # 480


def test_charge_ignore_lignes_sans_rpe_ou_duree():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "nom": ["A", "A"], "poste": ["P", "P"],
        "rpe": [6, np.nan], "duree_min": [60, 90],
    })
    charges = calculer_charges_quotidiennes(df)
    assert len(charges) == 1


# ------------------------------------------------------------
# 2. ACWR
# ------------------------------------------------------------

def test_acwr_charge_constante_donne_1():
    # 28 jours a 100 UA/jour : aigue = 700, chronique = 2800/4 = 700
    df = construire_seances([100.0] * 28)
    acwr = calculer_acwr_equipe(df)
    valides = acwr.dropna(subset=["acwr"])
    assert len(valides) == 1  # seul le jour 28 a 28 jours d'historique
    assert valides["acwr"].iloc[-1] == pytest.approx(1.0)


def test_acwr_pic_de_charge():
    # 21 jours a 100 puis 7 jours a 200 :
    # aigue = 1400 ; chronique = (21*100 + 7*200) / 4 = 875 ; ACWR = 1.6
    df = construire_seances([100.0] * 21 + [200.0] * 7)
    acwr = calculer_acwr_equipe(df)
    dernier = acwr.dropna(subset=["acwr"])["acwr"].iloc[-1]
    assert dernier == pytest.approx(1.6)


def test_acwr_absent_avant_28_jours():
    df = construire_seances([100.0] * 20)
    acwr = calculer_acwr_equipe(df)
    assert acwr["acwr"].isna().all()


def test_interpreter_acwr_zones():
    assert interpreter_acwr(np.nan)[0] == "Donnees insuffisantes"
    assert interpreter_acwr(0.5)[0] == "Charge en baisse marquee"
    assert interpreter_acwr(1.0)[0] == "Zone habituelle"
    assert interpreter_acwr(1.4)[0] == "Vigilance"
    assert "vigilance" in interpreter_acwr(1.8)[0].lower()


# ------------------------------------------------------------
# 3. Monotonie et contrainte (Foster)
# ------------------------------------------------------------

def test_monotonie_semaine_type():
    # Semaine : 6 jours a 100 UA + 1 jour leger a 10 UA.
    # Monotonie attendue = moyenne / ecart-type (ddof=1, comme pandas).
    df = construire_seances([100.0] * 6 + [10.0])
    monotonie = calculer_monotonie_contrainte(df)
    derniere = monotonie.dropna(subset=["monotonie"]).iloc[-1]

    moyenne = (6 * 100 + 10) / 7.0
    ecart = np.std([100] * 6 + [10], ddof=1)
    assert derniere["monotonie"] == pytest.approx(moyenne / ecart, rel=1e-6)
    assert derniere["contrainte"] == pytest.approx(
        (6 * 100 + 10) * moyenne / ecart, rel=1e-6
    )


def test_monotonie_absente_avant_7_jours():
    df = construire_seances([100.0, 50.0, 80.0])
    monotonie = calculer_monotonie_contrainte(df)
    assert monotonie["monotonie"].isna().all()


def test_monotonie_charge_uniforme_est_nan():
    # Charge identique chaque jour : ecart-type nul, monotonie indefinie
    df = construire_seances([100.0] * 10)
    monotonie = calculer_monotonie_contrainte(df)
    assert monotonie["monotonie"].isna().all()


# ------------------------------------------------------------
# 4. Hooper
# ------------------------------------------------------------

def test_hooper_somme_et_interpretation():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01"]), "nom": ["A"],
        "sommeil": [2], "fatigue": [3], "courbatures": [2], "stress": [3],
    })
    resultat = calculer_hooper(df)
    assert resultat["hooper"].iloc[0] == 10
    assert interpreter_hooper(10)[0] == "Bon etat"
    assert interpreter_hooper(16)[0] == "Etat moyen"
    assert interpreter_hooper(24)[0] == "Etat degrade"


# ------------------------------------------------------------
# 5. Z-scores
# ------------------------------------------------------------

def test_zscore_derniere_valeur_detecte_un_pic():
    dates = pd.Series(pd.date_range("2026-01-01", periods=29, freq="D"))
    valeurs = pd.Series([8.0, 12.0] * 14 + [16.0])  # ref : moyenne 10
    z, derniere = zscore_derniere_valeur(dates, valeurs)
    assert derniere == 16.0
    ecart = np.std([8.0, 12.0] * 14, ddof=1)
    assert z == pytest.approx((16.0 - 10.0) / ecart, rel=1e-6)


def test_zscore_derniere_valeur_reference_insuffisante():
    dates = pd.Series(pd.date_range("2026-01-01", periods=5, freq="D"))
    valeurs = pd.Series([10.0, 11.0, 9.0, 10.0, 15.0])
    z, derniere = zscore_derniere_valeur(dates, valeurs)
    assert z is None and derniere is None


def test_zscore_vs_historique_guards():
    serie_courte = pd.Series([10.0] * 10)
    assert zscore_vs_historique(serie_courte) == (None, None)
    serie_plate = pd.Series([10.0] * 40)  # ecart-type nul
    assert zscore_vs_historique(serie_plate) == (None, None)


# ------------------------------------------------------------
# 6. Croissance (regle des 60 jours)
# ------------------------------------------------------------

def test_croissance_utilise_reference_a_60_jours():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-31", "2026-04-01"]),
        "nom": ["A"] * 3,
        "taille_cm": [168.0, 168.5, 171.0],
        "masse_kg": [58.0, 58.2, 59.0],
    })
    croissance = calculer_croissance(df)
    vitesses = croissance["vitesse_cm_an"].tolist()

    assert np.isnan(vitesses[0])
    # Mesure 2 : seule reference possible a 30 j (< 60 j, repli assume)
    assert vitesses[1] == pytest.approx(0.5 / 30 * 365, rel=1e-6)
    # Mesure 3 : reference = mesure 2 (60 j d'ecart exactement)
    assert vitesses[2] == pytest.approx(2.5 / 60 * 365, rel=1e-6)


# ------------------------------------------------------------
# 7. Disponibilite : fusion des chevauchements (roadmap §11)
# ------------------------------------------------------------

def test_fusionner_intervalles_exemple_roadmap():
    # 1-10 mars + 5-15 mars = 15 jours uniques, pas 21
    a = (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-03-10"))
    b = (pd.Timestamp("2026-03-05"), pd.Timestamp("2026-03-15"))
    assert _fusionner_intervalles([a, b]) == 15
    assert _fusionner_intervalles([b, a]) == 15  # ordre indifferent
    assert _fusionner_intervalles([]) == 0


def construire_periode_seances(nom, debut, fin):
    return pd.DataFrame({
        "date": pd.to_datetime([debut, fin]),
        "nom": [nom, nom], "poste": ["P", "P"],
        "rpe": [5, 5], "duree_min": [60, 60],
    })


def test_disponibilite_episodes_chevauchants():
    seances = construire_periode_seances("A", "2026-03-01", "2026-03-31")
    blessures = pd.DataFrame({
        "date_debut": pd.to_datetime(["2026-03-01", "2026-03-05"]),
        "nom": ["A", "A"], "type": ["Blessure", "Blessure"],
        "zone": ["Cheville", "Genou"], "jours_absence": [10, 11],
    })
    resultat = calculer_disponibilite(blessures, seances)
    assert resultat["Jours d'absence"].iloc[0] == 15
    assert resultat["Disponibilite (%)"].iloc[0] == pytest.approx(
        (31 - 15) / 31 * 100, abs=0.1
    )


def test_disponibilite_episode_hors_periode_recadre():
    seances = construire_periode_seances("A", "2026-03-01", "2026-03-31")
    blessures = pd.DataFrame({
        # Commence le 25 fevrier, 10 jours -> seuls 1-6 mars comptent (6 j)
        "date_debut": pd.to_datetime(["2026-02-25"]),
        "nom": ["A"], "type": ["Blessure"],
        "zone": ["Dos"], "jours_absence": [10],
    })
    resultat = calculer_disponibilite(blessures, seances)
    assert resultat["Jours d'absence"].iloc[0] == 6
    assert resultat["Episodes"].iloc[0] == 1


def test_disponibilite_episode_duree_nulle_ignore():
    seances = construire_periode_seances("A", "2026-03-01", "2026-03-31")
    blessures = pd.DataFrame({
        "date_debut": pd.to_datetime(["2026-03-10"]),
        "nom": ["A"], "type": ["Maladie"], "zone": ["—"],
        "jours_absence": [0],
    })
    resultat = calculer_disponibilite(blessures, seances)
    assert resultat["Jours d'absence"].iloc[0] == 0
    assert resultat["Disponibilite (%)"].iloc[0] == 100.0


# ------------------------------------------------------------
# 8. Test d'integration leger sur les donnees de demonstration
# ------------------------------------------------------------

def test_alertes_individualisees_sur_demo():
    df = generer_donnees_demo()
    alertes = construire_alertes_individualisees(df)
    assert isinstance(alertes, list)
    for alerte in alertes:
        assert alerte["niveau"] in ("alerte", "attention")
        assert alerte["nom"].startswith("Joueuse")


# ------------------------------------------------------------
# 9. Centre d'alertes fusionne
# ------------------------------------------------------------

def test_toutes_alertes_demo_rouges_en_premier():
    from calculs import construire_toutes_alertes
    from donnees import generer_demo_bien_etre, generer_demo_anthropometrie

    alertes = construire_toutes_alertes(
        generer_donnees_demo(),
        generer_demo_bien_etre(),
        generer_demo_anthropometrie(),
    )
    assert len(alertes) > 0
    # Tri : aucune "attention" avant une "alerte"
    niveaux = [a["niveau"] for a in alertes]
    if "alerte" in niveaux:
        derniere_rouge = max(i for i, n in enumerate(niveaux) if n == "alerte")
        premiere_orange = min(
            (i for i, n in enumerate(niveaux) if n == "attention"),
            default=len(niveaux),
        )
        assert derniere_rouge < premiere_orange
    # La surcharge programmee de la Joueuse 5 est bien detectee
    modules_j5 = {a["module"] for a in alertes if a["nom"] == "Joueuse 5"}
    assert "ACWR" in modules_j5
    assert "Contrainte" in modules_j5


# ------------------------------------------------------------
# 10. Disponibilite : cas limites supplementaires
# ------------------------------------------------------------

def test_disponibilite_episode_couvrant_toute_la_periode():
    seances = construire_periode_seances("A", "2026-03-01", "2026-03-31")
    blessures = pd.DataFrame({
        "date_debut": pd.to_datetime(["2026-02-01"]),
        "nom": ["A"], "type": ["Blessure"], "zone": ["Genou"],
        "jours_absence": [90],  # couvre largement tout mars
    })
    resultat = calculer_disponibilite(blessures, seances)
    assert resultat["Jours d'absence"].iloc[0] == 31
    assert resultat["Disponibilite (%)"].iloc[0] == 0.0


# ------------------------------------------------------------
# 11. Jeux minimalistes : une joueuse, une semaine, tests absents
# ------------------------------------------------------------

def test_pipeline_une_joueuse_une_semaine_sans_crash():
    df = construire_seances([300.0, 0.0, 450.0, 0.0, 350.0, 500.0, 0.0])
    charges = calculer_charges_quotidiennes(df)
    assert charges["charge"].sum() == 1600.0
    acwr = calculer_acwr_equipe(df)
    assert acwr["acwr"].isna().all()  # < 28 jours : pas d'ACWR
    monotonie = calculer_monotonie_contrainte(df)
    assert len(monotonie) == 7


def test_progression_vide_si_moins_de_deux_tests():
    from calculs import calculer_progression
    df = construire_seances([100.0] * 5)
    for colonne in ["cmj_cm", "detente_attaque_cm", "detente_contre_cm",
                    "vitesse_10m_s", "t_test_s", "medecine_ball_cm",
                    "navette_s", "sauts"]:
        df[colonne] = np.nan
    assert calculer_progression(df, "Test") == {}
