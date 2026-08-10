# ============================================================
# tests/test_identites.py — Tests de l'identite des joueuses
# ============================================================

import pandas as pd

from identites import (
    appliquer_registre,
    construire_registre,
    detecter_orphelins,
    harmoniser_donnees,
    normaliser_cle,
)


# ------------------------------------------------------------
# 1. Cle canonique
# ------------------------------------------------------------

def test_cle_insensible_casse_accents_ponctuation():
    variantes = ["Salma B.", "salma b", "  SALMA  B. ", "Sàlma B", "Salma-B"]
    cles = {normaliser_cle(v) for v in variantes}
    assert cles == {"salma b"}


def test_cle_conserve_alphabets_non_latins():
    # Les noms en arabe ne doivent pas etre effaces par la normalisation
    assert normaliser_cle("سلمى") != ""
    assert normaliser_cle("سلمى") == normaliser_cle(" سلمى ")


def test_cles_differentes_restent_distinctes():
    # « Sara » et « Sarah » sont deux joueuses : jamais fusionnees
    assert normaliser_cle("Sara B.") != normaliser_cle("Sarah B.")


# ------------------------------------------------------------
# 2. Registre : orthographe canonique et identifiants
# ------------------------------------------------------------

def construire_df(noms):
    return pd.DataFrame({"nom": noms})


def test_registre_choisit_variante_la_plus_frequente():
    sources = {
        "seances": construire_df(["Salma B.", "Salma B.", "salma b."]),
    }
    registre, fusions = construire_registre(sources)
    assert registre["salma b"]["nom"] == "Salma B."
    assert len(fusions) == 1
    variantes, canonique = fusions[0]
    assert canonique == "Salma B."
    assert "salma b." in variantes


def test_registre_attribue_ids_stables():
    sources = {"seances": construire_df(["Bea", "Aya", "Chaima"])}
    registre, _ = construire_registre(sources)
    ids = {registre[cle]["nom"]: registre[cle]["athlete_id"]
           for cle in registre}
    # Ordre alphabetique des noms canoniques
    assert ids == {"Aya": "ATH-001", "Bea": "ATH-002", "Chaima": "ATH-003"}


# ------------------------------------------------------------
# 3. Harmonisation entre fichiers
# ------------------------------------------------------------

def test_harmonisation_repare_les_ecarts_entre_fichiers():
    donnees = {
        "seances": pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05", "2026-01-06"]),
            "nom": ["Salma B.", "Salma B."],
            "poste": ["Attaquante", "Attaquante"],
            "rpe": [6, 7], "duree_min": [90, 80],
        }),
        "bien_etre": pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05"]),
            "nom": ["salma b."],  # casse differente : donnees perdues avant
            "sommeil": [2], "fatigue": [3],
            "courbatures": [2], "stress": [2],
        }),
        "anthropometrie": None,
        "blessures": None,
    }
    harmonisees, registre, fusions, orphelins = harmoniser_donnees(donnees)

    # Le bien-etre est maintenant rattache a la bonne joueuse
    assert harmonisees["bien_etre"]["nom"].iloc[0] == "Salma B."
    assert len(fusions) == 1
    assert orphelins == []
    # Les originaux ne sont pas modifies
    assert donnees["bien_etre"]["nom"].iloc[0] == "salma b."


def test_orphelin_signale():
    donnees = {
        "seances": pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05"]),
            "nom": ["Salma B."], "poste": ["Attaquante"],
            "rpe": [6], "duree_min": [90],
        }),
        "bien_etre": pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05"]),
            "nom": ["Sallma B."],  # faute de frappe : aucune correspondance
            "sommeil": [2], "fatigue": [3],
            "courbatures": [2], "stress": [2],
        }),
        "anthropometrie": None,
        "blessures": None,
    }
    harmonisees, registre, fusions, orphelins = harmoniser_donnees(donnees)
    assert len(orphelins) == 1
    assert "Sallma B." in orphelins[0]
    assert "bien-etre" in orphelins[0]


def test_appliquer_registre_laisse_inconnus_intacts():
    registre = {"salma b": {"nom": "Salma B.", "athlete_id": "ATH-001"}}
    df = construire_df(["salma b.", "Aya K."])
    resultat = appliquer_registre(df, registre)
    assert resultat["nom"].tolist() == ["Salma B.", "Aya K."]


def test_detecter_orphelins_ignore_fichiers_absents():
    sources = {"seances": construire_df(["A"]), "bien-etre": None}
    registre_seances, _ = construire_registre(
        {"seances": construire_df(["A"])}
    )
    assert detecter_orphelins(sources, registre_seances) == []
