# ============================================================
# tests/test_securite.py — Garde-fous sur les fichiers importes
# ============================================================

import io

from donnees import valider_csv
from securite import (
    LIGNES_MAX,
    TAILLE_MAX_OCTETS,
    preparer_pour_validation,
    verifier_fichier_importe,
)


class FauxFichier(io.BytesIO):
    """Imite un UploadedFile Streamlit : BytesIO + attribut size +
    methode getvalue (heritee de BytesIO)."""

    def __init__(self, contenu, size=None):
        super().__init__(contenu)
        self.size = size if size is not None else len(contenu)


def test_fichier_none_rejete():
    texte, erreur = verifier_fichier_importe(None)
    assert texte is None
    assert erreur is not None


def test_fichier_vide_rejete():
    f = FauxFichier(b"", size=0)
    texte, erreur = verifier_fichier_importe(f)
    assert texte is None
    assert "vide" in erreur.lower()


def test_fichier_trop_gros_rejete_avant_parsing():
    f = FauxFichier(b"x", size=TAILLE_MAX_OCTETS + 1)
    texte, erreur = verifier_fichier_importe(f)
    assert texte is None
    assert "volumineux" in erreur.lower()


def test_fichier_valide_accepte():
    contenu = b"date,nom,poste,rpe,duree_min\n2026-01-05,Salma B.,Attaquante,6,90\n"
    f = FauxFichier(contenu)
    texte, erreur = verifier_fichier_importe(f)
    assert erreur is None
    assert "Salma" in texte


def test_trop_de_lignes_rejete():
    # En-tete + LIGNES_MAX + 1 lignes de donnees
    lignes = ["date,nom,poste,rpe,duree_min"]
    lignes += ["2026-01-05,J,P,6,90"] * (LIGNES_MAX + 1)
    contenu = ("\n".join(lignes)).encode("utf-8")
    f = FauxFichier(contenu)
    texte, erreur = verifier_fichier_importe(f)
    assert texte is None
    assert "lignes" in erreur.lower()


def test_encodage_latin1_gere():
    # « é » en latin-1 (0xE9) sans BOM utf-8
    contenu = "date,nom,poste,rpe,duree_min\n2026-01-05,Rémi,Passeur,6,90\n".encode(
        "latin-1"
    )
    f = FauxFichier(contenu)
    texte, erreur = verifier_fichier_importe(f)
    assert erreur is None
    assert "date" in texte


def test_preparer_pour_validation_chaine_vers_validateur():
    contenu = b"date,nom,poste,rpe,duree_min\n2026-01-05,Salma B.,Attaquante,6,90\n"
    f = FauxFichier(contenu)
    buffer, erreur = preparer_pour_validation(f)
    assert erreur is None
    df, erreurs, _ = valider_csv(buffer)
    assert erreurs == []
    assert len(df) == 1


def test_preparer_pour_validation_propage_le_rejet():
    f = FauxFichier(b"x", size=TAILLE_MAX_OCTETS + 1)
    buffer, erreur = preparer_pour_validation(f)
    assert buffer is None
    assert erreur is not None
