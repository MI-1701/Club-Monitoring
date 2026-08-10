# ============================================================
# tests/test_depot.py — Couche depot + saisie rapide atomique
# ============================================================

import io

import pandas as pd

from depot import DepotSession
from donnees import valider_csv, valider_saisie_tests
from identites import harmoniser_donnees


def construire_donnees():
    seances = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-05", "2026-01-06"]),
        "nom": ["Salma B.", "Aya K."],
        "poste": ["Attaquante", "Libero"],
        "rpe": [6, 5], "duree_min": [90, 80], "sauts": [40, 6],
        "cmj_cm": [pd.NA, pd.NA],
        "detente_attaque_cm": [pd.NA, pd.NA],
        "detente_contre_cm": [pd.NA, pd.NA],
        "vitesse_10m_s": [pd.NA, pd.NA],
        "t_test_s": [pd.NA, pd.NA],
        "medecine_ball_cm": [pd.NA, pd.NA],
        "navette_s": [pd.NA, pd.NA],
    })
    donnees = {"seances": seances, "bien_etre": None,
               "anthropometrie": None, "blessures": None}
    donnees, registre, _, _ = harmoniser_donnees(donnees)
    donnees["registre"] = registre
    return donnees


# ------------------------------------------------------------
# 1. Lectures du depot
# ------------------------------------------------------------

def test_depot_expose_les_joueuses_et_postes():
    depot = DepotSession(construire_donnees())
    assert depot.noms_joueuses() == ["Aya K.", "Salma B."]
    postes = depot.postes_par_joueuse()
    assert postes["Salma B."] == "Attaquante"
    assert postes["Aya K."] == "Libero"


# ------------------------------------------------------------
# 2. Ajout atomique (visible immediatement)
# ------------------------------------------------------------

def test_ajout_mesures_visible_dans_seances():
    donnees = construire_donnees()
    depot = DepotSession(donnees)
    avant = len(depot.seances())

    nb = depot.ajouter_mesures_tests([
        {"date": pd.Timestamp("2026-01-07"), "nom": "Salma B.",
         "poste": "Attaquante", "cmj_cm": 34.2},
    ])
    assert nb == 1
    apres = depot.seances()
    assert len(apres) == avant + 1
    # La nouvelle valeur est bien celle de Salma
    ligne = apres[(apres["nom"] == "Salma B.")
                  & (apres["cmj_cm"].notna())]
    assert float(ligne["cmj_cm"].iloc[0]) == 34.2


def test_export_csv_roundtrip():
    donnees = construire_donnees()
    depot = DepotSession(donnees)
    depot.ajouter_mesures_tests([
        {"date": pd.Timestamp("2026-01-07"), "nom": "Aya K.",
         "poste": "Libero", "cmj_cm": 30.0},
    ])
    csv_octets = depot.exporter_seances_csv()
    # Le CSV exporte doit repasser la validation metier sans erreur
    df, erreurs, _ = valider_csv(io.StringIO(csv_octets.decode("utf-8")))
    assert erreurs == []
    assert df["cmj_cm"].notna().sum() == 1


# ------------------------------------------------------------
# 3. Validation atomique de la saisie rapide (roadmap §16-17)
# ------------------------------------------------------------

def test_saisie_valide_toutes_les_lignes():
    lignes = [
        {"nom": "Salma B.", "poste": "Attaquante", "valeur": 34.2},
        {"nom": "Aya K.", "poste": "Libero", "valeur": 30.1},
    ]
    valides, erreurs = valider_saisie_tests(lignes, "cmj_cm")
    assert erreurs == []
    assert len(valides) == 2


def test_saisie_une_valeur_invalide_bloque_tout():
    lignes = [
        {"nom": "Salma B.", "poste": "Attaquante", "valeur": 34.2},
        {"nom": "Aya K.", "poste": "Libero", "valeur": 999.0},  # hors bornes
    ]
    valides, erreurs = valider_saisie_tests(lignes, "cmj_cm")
    assert len(erreurs) == 1
    assert "Aya K." in erreurs[0]
    # La valeur valide de Salma est bien reconnue, mais l'appelant
    # ne doit rien enregistrer tant qu'il reste une erreur.
    assert len(valides) == 1


def test_saisie_non_numerique_rejetee():
    lignes = [{"nom": "Salma B.", "poste": "Attaquante", "valeur": "abc"}]
    valides, erreurs = valider_saisie_tests(lignes, "cmj_cm")
    assert valides == []
    assert len(erreurs) == 1
    assert "nombre" in erreurs[0]


def test_saisie_cellules_vides_ignorees_sans_erreur():
    lignes = [
        {"nom": "Salma B.", "poste": "Attaquante", "valeur": None},
        {"nom": "Aya K.", "poste": "Libero", "valeur": ""},
        {"nom": "Ines M.", "poste": "Centrale", "valeur": 32.0},
    ]
    valides, erreurs = valider_saisie_tests(lignes, "cmj_cm")
    assert erreurs == []
    assert len(valides) == 1
    assert valides[0]["nom"] == "Ines M."


def test_saisie_accepte_virgule_decimale():
    lignes = [{"nom": "Salma B.", "poste": "Attaquante", "valeur": "34,2"}]
    valides, erreurs = valider_saisie_tests(lignes, "cmj_cm")
    assert erreurs == []
    assert valides[0]["cmj_cm"] == 34.2


def test_saisie_test_inconnu_rejete():
    valides, erreurs = valider_saisie_tests(
        [{"nom": "X", "poste": "Y", "valeur": 10}], "colonne_bidon"
    )
    assert valides == []
    assert len(erreurs) == 1
