# ============================================================
# tests/test_donnees.py — Tests de la validation des CSV
# ============================================================

import io

from donnees import (
    COLONNES_TESTS,
    generer_demo_anthropometrie,
    generer_demo_bien_etre,
    generer_demo_blessures,
    generer_donnees_demo,
    generer_modele_anthropometrie,
    generer_modele_bien_etre,
    generer_modele_blessures,
    generer_modele_csv,
    valider_csv,
    valider_csv_anthropometrie,
    valider_csv_bien_etre,
    valider_csv_blessures,
)


# ------------------------------------------------------------
# 1. Jeux de demonstration : structure attendue
# ------------------------------------------------------------

def test_demo_seances_structure():
    df = generer_donnees_demo()
    assert df["nom"].nunique() == 8
    for colonne in ["date", "nom", "poste", "rpe", "duree_min", "sauts"]:
        assert colonne in df.columns
    for colonne in COLONNES_TESTS:
        assert colonne in df.columns
    assert df["rpe"].between(1, 10).all()


def test_demo_modules_optionnels():
    assert len(generer_demo_bien_etre()) > 0
    assert len(generer_demo_anthropometrie()) > 0
    assert len(generer_demo_blessures()) > 0


# ------------------------------------------------------------
# 2. Les modeles CSV passent leur propre validation
# ------------------------------------------------------------

def test_modele_seances_valide():
    df, erreurs, _ = valider_csv(io.StringIO(generer_modele_csv()))
    assert erreurs == []
    assert len(df) == 3


def test_modele_bien_etre_valide():
    df, erreurs, _ = valider_csv_bien_etre(
        io.StringIO(generer_modele_bien_etre())
    )
    assert erreurs == []


def test_modele_anthropometrie_valide():
    df, erreurs, _ = valider_csv_anthropometrie(
        io.StringIO(generer_modele_anthropometrie())
    )
    assert erreurs == []


def test_modele_blessures_valide():
    df, erreurs, _ = valider_csv_blessures(
        io.StringIO(generer_modele_blessures())
    )
    assert erreurs == []


# ------------------------------------------------------------
# 3. Validation des seances : cas d'erreur
# ------------------------------------------------------------

def test_colonne_obligatoire_manquante():
    csv = "date,nom,rpe,duree_min\n2026-01-05,Salma B.,6,90\n"
    df, erreurs, _ = valider_csv(io.StringIO(csv))
    assert df is None
    assert any("poste" in e for e in erreurs)


def test_date_invalide_supprimee():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "pas-une-date,Salma B.,Attaquante,6,90\n"
        "2026-01-06,Salma B.,Attaquante,7,80\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert len(df) == 1
    assert any("date invalide" in a for a in avertissements)


def test_rpe_hors_bornes_exclu_de_la_charge():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,15,90\n"
        "2026-01-06,Salma B.,Attaquante,7,80\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert df["rpe"].isna().sum() == 1  # le RPE 15 est neutralise
    assert any("exclue" in a for a in avertissements)


def test_duree_negative_exclue():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,6,-30\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert df["duree_min"].isna().all()


def test_variantes_de_nom_signalees():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,6,90\n"
        "2026-01-06,salma b.,Attaquante,7,80\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert any("plusieurs facons" in a for a in avertissements)


def test_date_future_signalee_mais_conservee():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2030-01-05,Salma B.,Attaquante,6,90\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert len(df) == 1
    assert any("futur" in a for a in avertissements)


def test_fichier_vide_rejete():
    csv = "date,nom,poste,rpe,duree_min\n"
    df, erreurs, _ = valider_csv(io.StringIO(csv))
    assert df is None
    assert len(erreurs) > 0


# ------------------------------------------------------------
# 4. Validation bien-etre : valeurs hors echelle exclues
# ------------------------------------------------------------

def test_bien_etre_valeur_hors_echelle_exclue():
    csv = (
        "date,nom,sommeil,fatigue,courbatures,stress\n"
        "2026-01-05,Salma B.,9,3,2,2\n"
        "2026-01-06,Salma B.,3,3,2,2\n"
    )
    df, erreurs, avertissements = valider_csv_bien_etre(io.StringIO(csv))
    assert erreurs == []
    # La ligne avec sommeil=9 est retiree (valeur neutralisee puis dropna)
    assert len(df) == 1
    assert any("hors echelle" in a for a in avertissements)


# ------------------------------------------------------------
# 5. Cas limites du plan Sprint 1.5
# ------------------------------------------------------------

def test_rpe_bornes_1_et_10_conservees():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,1,90\n"
        "2026-01-06,Salma B.,Attaquante,10,80\n"
    )
    df, erreurs, _ = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert df["rpe"].notna().all()


def test_duree_zero_exclue():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,6,0\n"
    )
    df, erreurs, _ = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert df["duree_min"].isna().all()


def test_sauts_zero_est_valide():
    csv = (
        "date,nom,poste,rpe,duree_min,sauts\n"
        "2026-01-05,Aya K.,Libero,5,90,0\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert df["sauts"].iloc[0] == 0
    assert not any("sauts" in a for a in avertissements)


def test_nom_vide_supprime():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,,Attaquante,6,90\n"
        "2026-01-06,Salma B.,Attaquante,7,80\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert len(df) == 1
    assert any("sans nom" in a for a in avertissements)


def test_lignes_identiques_signalees_mais_conservees():
    csv = (
        "date,nom,poste,rpe,duree_min\n"
        "2026-01-05,Salma B.,Attaquante,6,90\n"
        "2026-01-05,Salma B.,Attaquante,6,90\n"
    )
    df, erreurs, avertissements = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert len(df) == 2
    assert any("identique" in a for a in avertissements)


def test_colonne_supplementaire_conservee():
    csv = (
        "date,nom,poste,rpe,duree_min,commentaire\n"
        "2026-01-05,Salma B.,Attaquante,6,90,bonne seance\n"
    )
    df, erreurs, _ = valider_csv(io.StringIO(csv))
    assert erreurs == []
    assert "commentaire" in df.columns
