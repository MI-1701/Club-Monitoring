# ============================================================
# tests/test_i18n.py — Tests for internationalization module
# ------------------------------------------------------------
# Prevents i18n regressions: missing keys, empty values,
# broken template interpolation.
# ============================================================

import pytest
from i18n import (
    TEXTES, TEXTES_ALERTES, ETIQUETTES_ACWR, MODULES_ALERTES,
    t, t_alerte, etiquette_acwr, module_alerte
)


# ------------------------------------------------------------
# 1. Key symmetry tests
# ------------------------------------------------------------

def test_textes_toutes_les_cles_existent_dans_les_deux_langues():
    """Chaque cle de TEXTES doit avoir une entree 'fr' ET 'en'."""
    for cle, entree in TEXTES.items():
        assert "fr" in entree, f"Cle '{cle}' manque la version francaise"
        assert "en" in entree, f"Cle '{cle}' manque la version anglaise"


def test_textes_alertes_toutes_les_cles_existent_dans_les_deux_langues():
    """Chaque cle de TEXTES_ALERTES doit avoir 'fr' ET 'en'."""
    for cle, entree in TEXTES_ALERTES.items():
        assert "fr" in entree, f"Alerte '{cle}' manque la version francaise"
        assert "en" in entree, f"Alerte '{cle}' manque la version anglaise"


def test_etiquettes_acwr_toutes_les_cles_existent_dans_les_deux_langues():
    """Chaque etiquette ACWR doit avoir 'fr' ET 'en'."""
    for cle, entree in ETIQUETTES_ACWR.items():
        assert "fr" in entree, f"Etiquette ACWR '{cle}' manque la version francaise"
        assert "en" in entree, f"Etiquette ACWR '{cle}' manque la version anglaise"


def test_modules_alertes_toutes_les_cles_existent_dans_les_deux_langues():
    """Chaque module d'alerte doit avoir 'fr' ET 'en'."""
    for cle, entree in MODULES_ALERTES.items():
        assert "fr" in entree, f"Module alerte '{cle}' manque la version francaise"
        assert "en" in entree, f"Module alerte '{cle}' manque la version anglaise"


# ------------------------------------------------------------
# 2. No empty values
# ------------------------------------------------------------

def test_textes_aucune_valeur_vide():
    """Aucune cle ne doit avoir une chaine vide."""
    for cle, entree in TEXTES.items():
        assert entree.get("fr", "").strip() != "", f"Cle '{cle}' a une valeur francaise vide"
        assert entree.get("en", "").strip() != "", f"Cle '{cle}' a une valeur anglaise vide"


def test_textes_alertes_aucune_valeur_vide():
    """Aucune alerte ne doit avoir une chaine vide."""
    for cle, entree in TEXTES_ALERTES.items():
        assert entree.get("fr", "").strip() != "", f"Alerte '{cle}' a une valeur francaise vide"
        assert entree.get("en", "").strip() != "", f"Alerte '{cle}' a une valeur anglaise vide"


def test_etiquettes_acwr_aucune_valeur_vide():
    """Aucune etiquette ACWR ne doit etre vide."""
    for cle, entree in ETIQUETTES_ACWR.items():
        assert entree.get("fr", "").strip() != "", f"Etiquette ACWR '{cle}' a une valeur francaise vide"
        assert entree.get("en", "").strip() != "", f"Etiquette ACWR '{cle}' a une valeur anglaise vide"


def test_modules_alertes_aucune_valeur_vide():
    """Aucun module d'alerte ne doit etre vide."""
    for cle, entree in MODULES_ALERTES.items():
        assert entree.get("fr", "").strip() != "", f"Module alerte '{cle}' a une valeur francaise vide"
        assert entree.get("en", "").strip() != "", f"Module alerte '{cle}' a une valeur anglaise vide"


# ------------------------------------------------------------
# 3. Template interpolation tests
# ------------------------------------------------------------

def test_interpolation_templates_textes():
    """Les templates de TEXTES avec {} doivent accepter l'interpolation."""
    import re
    for cle, entree in TEXTES.items():
        for lang in ["fr", "en"]:
            texte = entree.get(lang, "")
            # Trouver tous les placeholders {variable}
            variables = re.findall(r"\{(\w+)\}", texte)
            if variables:
                # Creer des valeurs factices pour chaque variable
                kwargs_factices = {var: "TEST" for var in variables}
                try:
                    resultat = texte.format(**kwargs_factices)
                    # Verifier qu'aucun placeholder ne reste
                    assert "{" not in resultat, \
                        f"Cle '{cle}' ({lang}) : interpolation incomplete avec {kwargs_factices}"
                except (KeyError, IndexError) as e:
                    pytest.fail(
                        f"Cle '{cle}' ({lang}) : erreur d'interpolation avec {kwargs_factices}: {e}"
                    )


def test_interpolation_templates_alertes():
    """Les templates de TEXTES_ALERTES doivent accepter l'interpolation."""
    import re
    for cle, entree in TEXTES_ALERTES.items():
        for lang in ["fr", "en"]:
            texte = entree.get(lang, "")
            variables = re.findall(r"\{(\w+)\}", texte)
            if variables:
                kwargs_factices = {var: "TEST" for var in variables}
                try:
                    resultat = texte.format(**kwargs_factices)
                    assert "{" not in resultat, \
                        f"Alerte '{cle}' ({lang}) : interpolation incomplete"
                except (KeyError, IndexError) as e:
                    pytest.fail(
                        f"Alerte '{cle}' ({lang}) : erreur d'interpolation: {e}"
                    )


# ------------------------------------------------------------
# 4. Function behavior tests
# ------------------------------------------------------------

def test_t_retourne_la_cle_si_manquante():
    """Si une cle n'existe pas, t() doit retourner la cle elle-meme."""
    import streamlit as st
    # Simuler une langue par defaut
    if "langue" not in st.session_state:
        st.session_state["langue"] = "fr"
    resultat = t("cle_inexistante_pour_test")
    assert resultat == "cle_inexistante_pour_test"


def test_t_interpolation_avec_kwargs():
    """t() doit interpoler correctement avec des kwargs."""
    import streamlit as st
    if "langue" not in st.session_state:
        st.session_state["langue"] = "fr"
    # Utiliser une cle existante avec interpolation
    resultat = t("seances_chargees", n=10, j=5)
    assert "10" in resultat
    assert "5" in resultat


def test_t_alerte_avec_params():
    """t_alerte() doit interpoler les parametres d'alerte."""
    import streamlit as st
    if "langue" not in st.session_state:
        st.session_state["langue"] = "fr"
    resultat = t_alerte("acwr", valeur=1.45, etiquette="Test")
    assert "1.45" in resultat
    assert "Test" in resultat


def test_etiquette_acwr_retourne_traduction():
    """etiquette_acwr() doit retourner une traduction valide."""
    import streamlit as st
    if "langue" not in st.session_state:
        st.session_state["langue"] = "fr"
    resultat = etiquette_acwr("vigilance")
    assert resultat in ["Vigilance", "Watch"]


def test_module_alerte_retourne_traduction():
    """module_alerte() doit retourner une traduction valide."""
    import streamlit as st
    if "langue" not in st.session_state:
        st.session_state["langue"] = "fr"
    resultat = module_alerte("ACWR")
    assert resultat == "ACWR"


# ------------------------------------------------------------
# 5. Coverage tests for main dictionaries
# ------------------------------------------------------------

def test_toutes_les_langues_ont_le_meme_nombre_de_cles():
    """FR et EN doivent avoir exactement les memes cles dans TEXTES."""
    cles_fr = set()
    cles_en = set()
    for cle, entree in TEXTES.items():
        if "fr" in entree:
            cles_fr.add(cle)
        if "en" in entree:
            cles_en.add(cle)

    manquantes_en = cles_fr - cles_en
    manquantes_fr = cles_en - cles_fr

    assert len(manquantes_en) == 0, f"Cles manquantes en anglais: {manquantes_en}"
    assert len(manquantes_fr) == 0, f"Cles manquantes en francais: {manquantes_fr}"
