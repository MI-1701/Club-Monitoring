# Changelog

Toutes les modifications notables de Clubs Monitoring sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et ce projet respecte le [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Unreleased]

### Ajouté
- Paramètre URL `?demo=true` : chargement automatique des données de démonstration (lien Fiverr).
- Panneau d'onboarding / état vide : bouton 1-clic « Charger les données de démo », guide visuel en 3 étapes et téléchargement des modèles CSV.
- Marquage des alertes comme traitées, avec note optionnelle, conservé en session.
- Section « Historique des alertes » dans le rapport PDF d'équipe.
- Branding des rapports PDF : upload d'un logo de club, en-tête professionnel, pied de page avec page numérotée et URL de l'application.
- Rapport de couverture (pytest-cov) dans la CI avec upload Codecov.

### Modifié
- Internationalisation complète (interface, alertes et rapports PDF) : 100 % FR/EN.
- Tous les messages d'erreur le plus précis possibles : nom de colonne, numéro de ligne et plage valide.
- DPI des graphiques PDF augmenté de 150 à 200 pour un rendu plus net.

---

## [v2.0] — Interface bilingue

### Ajouté
- Sélecteur de langue FR/EN dans la barre latérale (interface, alertes et rapports PDF).
- Couche Dépôt (`depot.py`) homogénéisée dans toutes les pages.
- Recadrage des jours d'absence sur la période des séances.
- Fichier `SECURITY.md` détaillant le modèle de sécurité.

### Déployé
- Publication de l'application sur Streamlit Community Cloud (`club-monitoring.streamlit.app`).

---

## [v1.0] — Lancement initial

### Ajouté
- Module charge d'entraînement : méthode séance-RPE (Foster), ACWR avec zones, monotonie et contrainte.
- Module bien-être quotidien : questionnaire de Hooper (sommeil, fatigue, courbatures, stress).
- Module charge de sauts : volume hebdomadaire par joueuse.
- Module croissance : vitesse en cm/an, détection des pics (Lloyd & Oliver).
- Journal des blessures : épisodes, jours d'absence, disponibilité.
- Alertes individualisées par Z-score (comparaison à la propre référence de chaque joueuse).
- Centre d'alertes fusionné et trié par gravité.
- Fiche joueuse avec vue 360° et 5 onglets thématiques.
- Saisie rapide avec validation atomique et export CSV.
- Rapports PDF : fiche individuelle et synthèse d'équipe.
- 69 tests unitaires (calculs, validation CSV, identités, sécurité, dépôt).
