# ============================================================
# identites.py — Identite des joueuses entre fichiers
# ------------------------------------------------------------
# Probleme resolu (plan Sprint 1.5) : le nom sert de cle de
# jointure entre les 4 fichiers CSV. « Salma B. », « salma b. »
# et « Salma B » designent la meme joueuse mais creaient des
# joueuses fantomes, et les donnees de bien-etre ou de blessures
# pouvaient etre silencieusement perdues si l'orthographe
# differait du fichier de seances.
#
# Solution : une cle canonique insensible a la casse, aux
# accents, a la ponctuation et aux espaces. Toutes les variantes
# d'un meme nom sont regroupees sous une orthographe canonique
# (la plus frequente), et chaque joueuse recoit un identifiant
# interne stable pour la session (ATH-001, ATH-002, ...).
#
# Les fichiers CSV du coach restent inchanges : l'identite est
# geree en interne, pas imposee a l'utilisateur.
# ============================================================

import re
import unicodedata


def normaliser_cle(nom):
    """Transforme un nom en cle canonique de comparaison.

    « Salma B. », « salma b », «  SALMA  B. » et « Sàlma B. »
    donnent tous la meme cle : « salma b ».
    Les alphabets non latins (arabe...) sont conserves tels quels.
    Un nom manquant (None / NaN) donne une cle vide, jamais fusionnee.
    """
    if nom is None or (isinstance(nom, float) and nom != nom):
        return ""
    texte = unicodedata.normalize("NFKD", str(nom))
    # Retirer les accents (marques combinantes)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = texte.casefold()
    # Ponctuation et tirets deviennent des espaces ; les lettres de
    # tous les alphabets (\w) sont conservees
    texte = re.sub(r"[^\w]+", " ", texte, flags=re.UNICODE)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


def construire_registre(sources):
    """Construit le registre des joueuses a partir des fichiers charges.

    Entree : dictionnaire {libelle: DataFrame ou None}, chaque
    DataFrame contenant une colonne « nom ».

    Sortie : (registre, fusions)
      registre : {cle: {"nom": orthographe canonique,
                        "athlete_id": "ATH-001"}}
      fusions  : liste de (variantes triees, orthographe canonique)
                 pour les noms ecrits de plusieurs facons.

    L'orthographe canonique est la variante la plus frequente
    (a egalite : la plus longue, puis l'ordre alphabetique).
    """
    occurrences = {}
    for libelle in sources:
        df = sources[libelle]
        if df is None or "nom" not in df.columns:
            continue
        comptes = df["nom"].value_counts()
        for variante in comptes.index:
            cle = normaliser_cle(variante)
            if cle == "":
                continue
            if cle not in occurrences:
                occurrences[cle] = {}
            if variante not in occurrences[cle]:
                occurrences[cle][variante] = 0
            occurrences[cle][variante] = (
                occurrences[cle][variante] + int(comptes[variante])
            )

    registre = {}
    fusions = []
    for cle in occurrences:
        variantes = occurrences[cle]
        classement = sorted(
            variantes.items(),
            key=lambda paire: (-paire[1], -len(paire[0]), paire[0]),
        )
        canonique = classement[0][0]
        registre[cle] = {"nom": canonique}
        if len(variantes) > 1:
            fusions.append((sorted(variantes), canonique))

    # Identifiants internes stables pour la session, dans l'ordre
    # alphabetique des noms canoniques
    cles_triees = sorted(registre, key=lambda c: registre[c]["nom"])
    for position, cle in enumerate(cles_triees):
        registre[cle]["athlete_id"] = "ATH-" + str(position + 1).zfill(3)

    return registre, fusions


def appliquer_registre(df, registre):
    """Remplace la colonne « nom » par l'orthographe canonique.

    Toute la suite de l'application (filtres, jointures, calculs)
    fonctionne alors sur une identite coherente entre fichiers.
    """
    if df is None or "nom" not in df.columns:
        return df

    resultat = df.copy()
    noms_canoniques = []
    for nom in resultat["nom"]:
        cle = normaliser_cle(nom)
        if cle in registre:
            noms_canoniques.append(registre[cle]["nom"])
        else:
            noms_canoniques.append(nom)
    resultat["nom"] = noms_canoniques
    return resultat


def detecter_orphelins(sources, registre_seances):
    """Signale les noms des fichiers optionnels qui ne correspondent
    a aucune joueuse du fichier de seances (meme apres normalisation) :
    leurs donnees seraient invisibles dans les fiches individuelles."""
    messages = []
    for libelle in sources:
        if libelle == "seances":
            continue
        df = sources[libelle]
        if df is None or "nom" not in df.columns:
            continue
        for variante in sorted(df["nom"].unique()):
            cle = normaliser_cle(variante)
            if cle != "" and cle not in registre_seances:
                messages.append(
                    "« " + str(variante) + " » (fichier " + libelle
                    + ") ne correspond a aucune joueuse du fichier "
                    + "seances : verifiez l'orthographe."
                )
    return messages


def harmoniser_donnees(donnees):
    """Point d'entree : harmonise les 4 jeux de donnees.

    Entree : dictionnaire {seances, bien_etre, anthropometrie,
    blessures} tel que construit par l'application.

    Sortie : (donnees harmonisees, registre, fusions, orphelins).
    Les DataFrames d'origine ne sont pas modifies (copies).
    """
    sources = {
        "seances": donnees.get("seances"),
        "bien-etre": donnees.get("bien_etre"),
        "anthropometrie": donnees.get("anthropometrie"),
        "blessures": donnees.get("blessures"),
    }

    registre, fusions = construire_registre(sources)

    registre_seances, _ = construire_registre(
        {"seances": donnees.get("seances")}
    )
    orphelins = detecter_orphelins(sources, registre_seances)

    harmonisees = {
        "seances": appliquer_registre(donnees.get("seances"), registre),
        "bien_etre": appliquer_registre(donnees.get("bien_etre"), registre),
        "anthropometrie": appliquer_registre(
            donnees.get("anthropometrie"), registre
        ),
        "blessures": appliquer_registre(donnees.get("blessures"), registre),
    }

    return harmonisees, registre, fusions, orphelins
