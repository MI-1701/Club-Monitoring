# Sprint 2 — Sécurité, Saisie rapide, couche dépôt (roadmap Déploiement & Sécurité)

## Décision : PostgreSQL reporté, seam de persistance à la place

Tu as demandé « commencer à introduire PostgreSQL ». Refusé **à ce
stade**, pour les raisons que la roadmap elle-même donne (§21, §22,
§24 : « ne pas ajouter PostgreSQL juste parce que ça fait plus
professionnel », « ne pas ajouter l'authentification avant un vrai
besoin multi-utilisateur »). Détail dans `STORAGE.md`.

À la place : **couche dépôt (`depot.py`)** — une interface unique
(`DepotDonnees`) entre l'interface et les données. Aujourd'hui
`DepotSession` l'adosse aux DataFrames en mémoire ; demain
`DepotPostgres` la remplacera **sans toucher une seule page**. C'est
l'objectif du §21 (« concevoir le modèle interne pour qu'une base
puisse être introduite plus tard sans réécrire l'application ») sans
prendre la responsabilité d'héberger des données de santé de mineures.
Une esquisse commentée de `DepotPostgres` est en bas de `depot.py`.

## Sécurité (roadmap §8-13)

- **`securite.py`** : garde-fou taille (10 Mo), fichier vide,
  bombe de lignes (> 100 000), encodage utf-8/latin-1, **avant** tout
  parsing. Les 4 imports passent par `preparer_pour_validation` →
  validateur métier. Aucune désérialisation (§12).
- **`.streamlit/config.toml`** : `maxUploadSize = 10`, XSRF activé,
  télémétrie désactivée.
- **`.gitignore` durci** (§8) : `.env`, `.streamlit/secrets.toml`,
  `data/private/`, `data/real/`, `*_reel.csv` — les données réelles et
  les secrets ne peuvent plus être committés par accident.
- **`.streamlit/secrets.toml.example`** (§9) : gabarit ; le vrai
  fichier est ignoré. L'app n'utilise aucun secret aujourd'hui.
- **`SECURITY.md`** : modèle de sécurité, ce qui est en place, ce qui
  est reporté et pourquoi, signalement de vulnérabilité.
- **Énoncé de confidentialité in-app** (§13) : expander dans la barre
  latérale avec la formulation exacte demandée (« traitées en mémoire
  pendant la session… ne les persiste dans aucune base »). Plus de
  claim « aucune donnée stockée » non nuancé.
- **Bannière mode démo** (§14, §19) : bandeau « Données de
  démonstration » quand aucun CSV n'est importé.

## Saisie rapide (roadmap §16-17)

Nouvelle page **Saisie rapide** : l'entraîneur choisit un test + une
date, saisit les résultats de toute l'équipe dans une grille
(`st.data_editor`) pré-remplie avec l'effectif, puis :

```
Éditer → Valider TOUT → Aperçu → Confirmer → Export CSV
```

- **Atomique** (§17) : `valider_saisie_tests` vérifie chaque valeur
  (numérique, bornes de plausibilité par test). S'il reste **une**
  erreur, rien n'est enregistré — pas de fusion partielle. Le compteur
  affiche « ✓ 10/12 valides » et liste les corrections.
- Cellule vide = joueuse non testée : ignorée sans erreur. Accepte la
  virgule décimale.
- Confirmation → ajout **en mémoire** via le dépôt → visible
  immédiatement dans les fiches et les alertes → **export du CSV
  séances mis à jour**. En mode démo, un avertissement rappelle que les
  valeurs restent en session : télécharger le CSV pour les conserver.
- Cohérent avec l'architecture sans stockage : la persistance, c'est le
  fichier que le coach re-télécharge et re-importe.

## Tests : 52 → 69

- `tests/test_securite.py` (8) : none/vide/trop gros/trop de lignes,
  latin-1, passage au validateur, propagation du rejet.
- `tests/test_depot.py` (11) : lectures du dépôt, ajout visible
  immédiatement, export re-validé, **validation atomique** (une valeur
  aberrante bloque le lot), cellules vides ignorées, virgule décimale,
  test inconnu rejeté.
- Bout-à-bout vérifié hors tests : saisie → la progression CMJ lue par
  les calculs change bien → export re-valide (513 lignes).

Ruff + compileall verts.

## Ordre de nav revu

Vue d'équipe · Fiche joueuse · **Saisie rapide** · Bien-être ·
Comparaison · Rapports PDF · Méthode. La fiche (vue 360) et la saisie
sont remontées : ce sont les écrans qu'un coach utilise le plus.

## Non fait, volontairement

- **PostgreSQL / auth / RBAC** : voir `STORAGE.md`. Le seam est prêt ;
  la base ne s'active qu'avec un vrai besoin multi-utilisateur, et
  alors l'auth se fait dans le même sprint.
- **Landing page dédiée (§18-19)** : la bannière démo suffit pour les
  captures Fiverr ; une vraie page d'accueil est du polish, pas de la
  sécurité.
