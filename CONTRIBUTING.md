# Contribuer à Clubs Monitoring

Merci de votre intérêt pour ce projet. Ce document explique comment démarrer, proposer des modifications et les standards de qualité.

---

## Cadre du projet

Clubs Monitoring est un outil de monitoring physique pour le volley-ball. Toutes les données importées restent en mémoire (aucune base de données persistante) pour protéger la confidentialité des athlètes, notamment les mineurs.

---

## Configuration du poste de développement

### Prérequis

- Python 3.11 ou supérieur
- pip

### Installation

```bash
git clone https://github.com/MI-1701/Clubs-Monitoring.git
cd Clubs-Monitoring
pip install -r requirements.txt -r requirements-dev.txt
```

### Lancer en local

```bash
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

---

## Lancer les tests et le linting

```bash
# Tous les tests
pytest -q

# Avec rapport de couverture
pytest --cov=. --cov-report=term-missing -q

# Linting
ruff check .
```

La couverture cible est ≥ 80 %.

---

## Cycle de travail

1. Créer une branche depuis `main` :
   ```bash
   git checkout -b feature/nom-de-la-fonctionnalite
   ```
2. Écrire le code et les tests associés.
3. S'assurer que `pytest -q` et `ruff check .` passent sans erreur.
4. Pusher et ouvrir une Pull Request vers `main`.

---

## Standards de code

- **Internationalisation** : Tout texte visible par l'utilisateur doit passer par `t(cle)` depuis `i18n.py`. Ajouter les clés dans les deux langues (FR et EN). Les tests `test_i18n.py` vérifient automatiquement la symétrie.
- **Couche Dépôt** : Les pages Streamlit ne doivent accéder aux données que via l'interface `depot.seances()`, `depot.bien_etre()`, etc. — jamais via un dictionnaire `donnees["clé"]` direct.
- **Tests** : Toute nouvelle fonctionnalité de calcul doit inclure au moins un test. Les tests de validation doivent couvrir les cas limites.
- **Variables** : Les noms de variables restent en français pour rester cohérent avec le vocabulaire métier du projet.

---

## Structure du projet

| Fichier | Rôle |
|---|---|
| `app.py` | Interface Streamlit (7 vues) |
| `donnees.py` | Génération de données de démo, modèles CSV, validation |
| `identites.py` | Harmonisation des noms de joueuses entre fichiers |
| `securite.py` | Garde-fous sur les fichiers importés (taille, encodage, lignes) |
| `depot.py` | Couche Repository (interface abstraite + implémentation session) |
| `i18n.py` | Dictionnaires FR/EN et gabarits d'alertes |
| `calculs.py` | Moteur scientifique (ACWR, Hooper, Z-scores, croissance) |
| `rapport_pdf.py` | Génération des rapports PDF (ReportLab + Matplotlib) |
| `tests/` | Tests unitaires des calculs et de la validation |

---

## Proposer un bug

Ouvrir une issue sur GitHub en décrivant :
- Ce que vous avez fait
- Ce qui s'est passé
- Ce que vous attendiez

Joindre une capture d'écran si pertinent.

---

## Licences et données

Ce projet est conçu pour des données fictives ou anonymisées. Ne jamais déposer de données réelles d'athlètes mineures sur la démonstration publique.
