# ============================================================
# depot.py — Couche d'acces aux donnees (repository)
# ------------------------------------------------------------
# POURQUOI CE FICHIER EXISTE
#
# L'application ne stocke rien de facon persistante : les CSV
# sont traites en memoire pendant la session (choix assume,
# adapte a un demonstrateur public de donnees de mineures).
#
# Mais la roadmap (§21) demande de « concevoir le modele interne
# pour qu'une base de donnees puisse etre introduite plus tard
# sans reecrire l'application ». C'est exactement le role de ce
# fichier : un SEUL point de passage entre l'interface et les
# donnees. Aujourd'hui il enveloppe des DataFrames en session ;
# demain, une sous-classe DepotPostgres pourra le remplacer sans
# qu'aucune page Streamlit ne change.
#
#   Interface (DepotDonnees)
#         │
#         ├── DepotSession   ← aujourd'hui : DataFrames en memoire
#         └── DepotPostgres  ← plus tard : meme interface, SQL
#
# Tant qu'il n'y a ni comptes, ni multi-club, ni besoin de
# conserver les donnees entre sessions, brancher une vraie base
# serait prematuré (et transformerait un demonstrateur en
# hebergeur de donnees de sante de mineures — voir STORAGE.md).
# ============================================================

import pandas as pd


class DepotDonnees:
    """Interface commune. Une implementation concrete fournit
    l'acces aux quatre jeux (seances, bien-etre, anthropometrie,
    blessures) et l'ajout atomique de nouvelles mesures."""

    def seances(self):
        raise NotImplementedError

    def bien_etre(self):
        raise NotImplementedError

    def anthropometrie(self):
        raise NotImplementedError

    def blessures(self):
        raise NotImplementedError

    def registre(self):
        raise NotImplementedError

    def noms_joueuses(self):
        """Liste triee des noms canoniques presents dans les seances."""
        df = self.seances()
        if df is None or "nom" not in df.columns:
            return []
        return sorted(df["nom"].unique())

    def postes_par_joueuse(self):
        """Dictionnaire nom -> dernier poste connu."""
        df = self.seances()
        resultat = {}
        if df is None:
            return resultat
        for nom in df["nom"].unique():
            postes = df[df["nom"] == nom]["poste"]
            if len(postes) > 0:
                resultat[nom] = postes.iloc[-1]
        return resultat

    def ajouter_mesures_tests(self, lignes):
        """Ajoute des lignes de tests (atomique). A implementer."""
        raise NotImplementedError

    def exporter_seances_csv(self):
        """Renvoie le CSV complet des seances (bytes) pour export."""
        raise NotImplementedError


class DepotSession(DepotDonnees):
    """Implementation en memoire, portee : la session Streamlit.

    Enveloppe le dictionnaire `donnees` deja construit par
    l'application (seances, bien_etre, anthropometrie, blessures,
    registre). Aucune ecriture disque, aucune persistance.
    """

    def __init__(self, donnees):
        self._donnees = donnees

    def seances(self):
        return self._donnees.get("seances")

    def bien_etre(self):
        return self._donnees.get("bien_etre")

    def anthropometrie(self):
        return self._donnees.get("anthropometrie")

    def blessures(self):
        return self._donnees.get("blessures")

    def registre(self):
        return self._donnees.get("registre", {})

    def ajouter_mesures_tests(self, lignes):
        """Ajoute une liste de lignes de tests au DataFrame seances,
        EN MEMOIRE et de facon atomique : soit toutes les lignes sont
        integrees, soit aucune (voir Depot.appliquer_ajout ci-dessous).

        `lignes` : liste de dictionnaires deja valides, chacun avec au
        minimum date, nom, poste et une ou plusieurs colonnes de tests.

        Retourne le nombre de lignes ajoutees.
        """
        if len(lignes) == 0:
            return 0

        seances = self._donnees.get("seances")
        if seances is None:
            raise ValueError("Aucune donnee de seances a completer.")

        nouvelles = pd.DataFrame(lignes)
        nouvelles["date"] = pd.to_datetime(nouvelles["date"])

        # Aligner les colonnes sur le schema existant
        for colonne in seances.columns:
            if colonne not in nouvelles.columns:
                nouvelles[colonne] = pd.NA
        nouvelles = nouvelles[seances.columns]

        fusion = pd.concat([seances, nouvelles], ignore_index=True)
        fusion = fusion.sort_values(["nom", "date"]).reset_index(drop=True)

        # Remplacement atomique de la reference en session
        self._donnees["seances"] = fusion
        return len(nouvelles)

    def exporter_seances_csv(self):
        seances = self._donnees.get("seances")
        if seances is None:
            return b""
        export = seances.copy()
        if "date" in export.columns:
            export["date"] = pd.to_datetime(
                export["date"]
            ).dt.strftime("%Y-%m-%d")
        return export.to_csv(index=False).encode("utf-8")


# ------------------------------------------------------------
# ESQUISSE — a activer seulement quand une vraie base est requise
# ------------------------------------------------------------
# class DepotPostgres(DepotDonnees):
#     """Meme interface, adossee a PostgreSQL. Ne pas activer tant
#     qu'il n'y a pas de besoin multi-utilisateur reel : cela
#     impliquerait authentification, RBAC, chiffrement et gestion
#     du cycle de vie des donnees de mineures (voir STORAGE.md)."""
#
#     def __init__(self, connexion):
#         self._connexion = connexion
#
#     def seances(self):
#         return pd.read_sql("SELECT * FROM seances", self._connexion)
#     ...
