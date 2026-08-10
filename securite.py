# ============================================================
# securite.py — Traitement securise des fichiers importes
# ------------------------------------------------------------
# Un fichier envoye par l'utilisateur est une donnee non fiable
# (roadmap securite §10). Ce module applique les garde-fous
# AVANT que le contenu n'atteigne les validateurs metier :
#   1. taille maximale (§11)
#   2. lecture en CSV uniquement — jamais de pickle/eval (§12)
#   3. garde-fou sur le nombre de lignes (bombe de decompression)
#
# Les validateurs de donnees.py prennent le relais ensuite pour
# les colonnes, les types et les bornes.
# ============================================================

import io

# Limite alignee sur .streamlit/config.toml (maxUploadSize = 10).
# Les CSV de monitoring reels pesent quelques dizaines de Ko ;
# 10 Mo est deja tres large et protege des envois accidentels.
TAILLE_MAX_OCTETS = 10 * 1024 * 1024

# Un CSV de saison pour un gros club : ~40 joueuses x 200 seances
# x 4 fichiers reste bien sous 100 000 lignes. Au-dela, on refuse
# avant de charger en memoire.
LIGNES_MAX = 100_000


def verifier_fichier_importe(fichier):
    """Controle un objet fichier Streamlit AVANT parsing.

    Retourne (contenu_texte, erreur). Si erreur est non-None, le
    fichier doit etre rejete sans autre traitement.

    Ne fait AUCUNE deserialisation : le contenu est lu comme du
    texte brut et repasse ensuite par pandas.read_csv cote metier.
    """
    if fichier is None:
        return None, "Aucun fichier fourni."

    # 1. Taille — l'attribut size existe sur les UploadedFile Streamlit ;
    #    on retombe sur la lecture du buffer si absent.
    taille = getattr(fichier, "size", None)
    if taille is None:
        position = fichier.tell()
        fichier.seek(0, io.SEEK_END)
        taille = fichier.tell()
        fichier.seek(position)

    if taille > TAILLE_MAX_OCTETS:
        mo = round(taille / (1024 * 1024), 1)
        return None, (
            "Fichier trop volumineux (" + str(mo) + " Mo). "
            "Limite : 10 Mo. Un CSV de monitoring normal fait "
            "quelques dizaines de Ko."
        )

    if taille == 0:
        return None, "Fichier vide."

    # 2. Lecture en texte (utf-8, repli latin-1) — jamais de pickle.
    try:
        octets = fichier.getvalue()
    except AttributeError:
        fichier.seek(0)
        octets = fichier.read()

    if isinstance(octets, bytes):
        try:
            texte = octets.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                texte = octets.decode("latin-1")
            except UnicodeDecodeError:
                return None, (
                    "Encodage du fichier illisible. "
                    "Enregistrez le CSV en UTF-8."
                )
    else:
        texte = str(octets)

    # 3. Garde-fou sur le nombre de lignes
    nb_lignes = texte.count("\n")
    if nb_lignes > LIGNES_MAX:
        return None, (
            "Fichier a " + str(nb_lignes) + " lignes : au-dela de la "
            "limite de " + str(LIGNES_MAX) + ". Verifiez le fichier."
        )

    return texte, None


def preparer_pour_validation(fichier):
    """Verifie le fichier puis renvoie un buffer texte pret a etre
    passe aux valider_csv_* de donnees.py.

    Retourne (buffer, erreur). buffer est un io.StringIO si le
    fichier est accepte, sinon None avec un message d'erreur.
    """
    texte, erreur = verifier_fichier_importe(fichier)
    if erreur is not None:
        return None, erreur
    return io.StringIO(texte), None
