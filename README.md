# Clubs Monitoring — Monitoring physique complet pour le volleyball

Système de monitoring **charge · bien-être · sauts · croissance · blessures**
avec **alertes individualisées** pour équipes de volleyball. Conçu sur le
terrain avec les U17 du FUS-VB, utilisable par n'importe quel club via de
simples fichiers CSV — nom du club personnalisable en un clic.

> **Démo en ligne : [club-monitoring.streamlit.app](https://club-monitoring.streamlit.app)**

![CI](https://github.com/MI-1701/Clubs-Monitoring/actions/workflows/ci.yml/badge.svg)

![Coverage](https://codecov.io/gh/MI-1701/Clubs-Monitoring/branch/main/graph/badge.svg)

---

## Les 6 modules

1. **Charge d'entraînement** — séance-RPE (Foster), ACWR avec zones de
   risque, monotonie et contrainte
2. **Bien-être quotidien** — questionnaire de Hooper (sommeil, fatigue,
   courbatures, stress), matrice d'équipe du jour
3. **Charge de sauts** — volume hebdomadaire par joueuse, vigilance
   tendinopathie rotulienne
4. **Croissance** — vitesse en cm/an, détection des pics de croissance
   (Lloyd & Oliver)
5. **Journal des blessures** — épisodes, jours d'absence, disponibilité
6. **Alertes individualisées** — chaque joueuse est comparée à sa propre
   référence (Z-scores), pas à des seuils universels

Le **centre d'alertes** fusionne tous les signaux et les trie par gravité.


## Aperçu

**Vue d'équipe — le centre d'alertes fusionne tous les signaux**
![Centre d'alertes](Pictures/vue_equipe_1.png)

**Synthèse par joueuse et disponibilité**
![Synthèse](Pictures/vue_equipe_2.png)

**Bien-être quotidien — la matrice du matin de l'entraîneur**
![Matrice bien-être](Pictures/bien_etre_1.png)

**Fiche joueuse — batterie internationale de 7 tests**
![Fiche joueuse](Pictures/fiche_joueuse_1.png)

**Charge d'entraînement — ACWR, monotonie et contrainte**
![Charge et ACWR](Pictures/fiche_joueuse_3.png)

**Comparaison — détente d'attaque de toute l'équipe**
![Comparaison](Pictures/comparaison_3.png)


## Interface

**Interface bilingue FR / EN** : un sélecteur de langue dans la barre
latérale bascule toute l'application — pages, alertes et rapports PDF —
entre français et anglais.


Vue d'équipe · Fiche joueuse (vue 360 + 5 onglets) · **Saisie rapide**
(un test pour toute l'équipe, validation atomique, export CSV) ·
Bien-être · Comparaison · Rapports PDF · Méthode et références.
La page Méthode documente chaque indicateur, ses seuils et ses limites.

## Méthode scientifique

Séance-RPE (Foster, 2001) · ACWR lu comme signal de vigilance, zone de
référence 0,80–1,30 (Gabbett, 2016 ; critique : Impellizzeri, 2020) ·
Monotonie/contrainte (Foster) · Indice de Hooper
(Hooper & Mackinnon, 1995) · Pics de croissance (Lloyd & Oliver, 2012) ·
Charge de sauts et tendinopathie (Bahr & Visnes). Tests suivis : CMJ, détente d'attaque, détente de contre, sprint 10 m,
T-test, lancer de médecine-ball, navette volleyball.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déployer gratuitement (Streamlit Community Cloud)

1. Poussez ce dossier sur un dépôt GitHub
2. Allez sur [share.streamlit.io](https://share.streamlit.io) et connectez
   votre compte GitHub
3. **New app** → sélectionnez le dépôt, branche `main`, fichier `app.py`
4. **Deploy** — les dépendances de `requirements.txt` s'installent
   automatiquement

## Format des données

4 fichiers CSV, dont un seul obligatoire. Les modèles avec exemples se
téléchargent dans la barre latérale de l'application.

| Fichier | Statut | Colonnes |
|---|---|---|
| `seances.csv` | obligatoire |date, nom, poste, rpe, duree_min, sauts, cmj_cm, detente_attaque_cm, detente_contre_cm, vitesse_10m_s, t_test_s, medecine_ball_cm, navette_s |
| `bien_etre.csv` | optionnel | date, nom, sommeil, fatigue, courbatures, stress (1-7) |
| `anthropometrie.csv` | optionnel | date, nom, taille_cm, masse_kg |
| `blessures.csv` | optionnel | date_debut, nom, type, zone, jours_absence |

Chaque module absent est simplement masqué : l'application fonctionne
avec le seul fichier de séances. Les noms sont **harmonisés
automatiquement entre fichiers** (casse, accents, ponctuation) ; les
variantes regroupées et les noms sans correspondance sont signalés
dans la barre latérale.

## Qualité du code

Les calculs scientifiques sont couverts par une suite de tests unitaires
(ACWR, monotonie/contrainte, indice de Hooper, Z-scores, vitesse de
croissance, disponibilité avec fusion des épisodes qui se chevauchent)
et vérifiés à chaque commit par GitHub Actions (ruff + pytest).

```bash
pip install -r requirements-dev.txt
pytest -q        # 69 tests
ruff check .
```

## Confidentialité

Les fichiers CSV importés sont traités **en mémoire pendant la
session** ; l'application ne les persiste dans aucune base de données.
Le club reste l'unique détenteur de ses données — un point important
pour le suivi de jeunes athlètes. L'hébergement (Streamlit Community
Cloud) fournit le HTTPS ; voir `SECURITY.md`.

## Structure du projet

```
app.py                    Interface Streamlit (6 pages)
donnees.py                Données de démo, modèles CSV, validation des imports
identites.py              Identité des joueuses entre fichiers (clés canoniques)
securite.py               Garde-fous sur les fichiers importés (taille, encodage)
depot.py                  Couche d'accès aux données (prête pour une base future)
i18n.py                   Traductions FR / EN (interface, alertes, PDF)
calculs.py                Charge séance-RPE, ACWR, progression, alertes
rapport_pdf.py            Génération des rapports PDF (reportlab + matplotlib)
tests/                    Tests unitaires des calculs et de la validation
.github/workflows/ci.yml  Intégration continue (ruff + pytest)
```

## Auteur

**Ilias Moudrikah** — Préparateur physique adjoint FUS-VB, Master
Transformation Digitale & Technologies du Sport (Université Hassan
Premier, Settat) , Licence Professionelle Entrainement Sportif 
Specialité VolleyBall(IRFC, Institut Royal de Formation des Cadres, Sale Maamoura).

*L'ACWR est un indicateur de vigilance destiné à orienter l'attention de
l'entraîneur ; il ne remplace ni le jugement du staff ni l'avis médical.*
