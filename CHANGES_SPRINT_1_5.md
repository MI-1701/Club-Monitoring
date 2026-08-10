# Sprint 1.5 — Identité des joueuses + vue 360 (plan « Next Move »)

## Décision d'architecture : l'objectif du plan, pas sa lettre

Le plan §3–4 demandait des `athlete_id` visibles (ATH-000124) et des
mesures au format long (`athlete_id, date, test, value, unit`) dans les
CSV. **Refusé tel quel** : cela obligerait chaque coach à maintenir un
fichier d'effectif et à saisir des clés étrangères — la simplicité des
4 CSV est ce qui rend l'outil vendable. L'objectif réel (identité
robuste aux fautes de casse, d'accents, de ponctuation) est atteint
autrement :

## Nouveau module : `identites.py`

- **Clé canonique** insensible à la casse, aux accents, à la
  ponctuation et aux espaces : « Salma B. », « salma b », « Sàlma-B »
  → même joueuse. Les alphabets non latins (arabe) sont préservés.
- **Harmonisation entre les 4 fichiers** au chargement : les variantes
  d'un même nom sont regroupées sous l'orthographe la plus fréquente.
  Avant : un bien-être saisi « salma b. » était **silencieusement
  invisible** sur la fiche de « Salma B. ». C'était une vraie perte de
  données, pas un détail cosmétique.
- **Orphelins signalés** : un nom du bien-être/anthropométrie/blessures
  sans correspondance dans les séances (« Sallma B. ») déclenche un
  avertissement au lieu de disparaître. Fautes proches jamais
  fusionnées automatiquement (« Sara » ≠ « Sarah ») : on signale, on ne
  devine pas.
- **Identifiants internes** ATH-001… attribués par session
  (`donnees["registre"]`) : la fondation demandée par le plan, prête
  pour l'entrée rapide de tests et les exports, sans charge pour
  l'utilisateur.
- Les CSV du coach et les originaux en mémoire ne sont jamais modifiés
  (copies) ; les regroupements sont affichés dans la barre latérale.

## Fiche joueuse → vue 360 (plan §11–12, partiel)

- **Bandeau d'état instantané** en tête de fiche : ACWR du jour,
  Hooper du jour, disponibilité, nombre d'alertes actives — puis les
  alertes de la joueuse elle-même. Les 5 questions du plan (qui,
  performance, tolérance, changements, quoi investiguer) ont une
  réponse avant d'ouvrir un onglet.
- L'ACWR n'est plus calculé deux fois sur la page (plan §6).

## Refactor : `construire_toutes_alertes` (calculs.py)

La fusion ACWR + alertes individualisées vivait dans l'interface
(app.py). Déplacée dans la couche calculs, triée rouges d'abord,
réutilisée par la vue d'équipe **et** la fiche joueuse, couverte par
un test sur la démo (la surcharge programmée de la Joueuse 5 est
détectée : Contrainte rouge Z=+4.4, ACWR 1.48, pic de sauts).

## Validation (plan §10)

- Lignes **sans nom** supprimées (avec avertissement) — y compris le
  cas NaN réel du dtype chaîne de pandas 3.
- Lignes **strictement identiques** signalées mais conservées : un
  doublon de copier-coller doublerait la charge, mais deux séances
  identiques un jour de tournoi sont possibles — on alerte, on ne
  supprime pas silencieusement.

## Tests : 33 → 52

Nouveaux : normalisation des clés (casse/accents/arabe), choix de
l'orthographe canonique, réparation inter-fichiers, orphelins, IDs
stables, alertes fusionnées sur la démo, blessure couvrant toute la
période (disponibilité 0 %), RPE aux bornes 1 et 10, durée 0, sauts 0
valide, nom vide, doublons stricts, colonne supplémentaire conservée,
pipeline une joueuse/une semaine, progression vide. Ruff et compileall
verts.

## Reporté, volontairement

- **Schémas formels (plan §9)** : à cette échelle, les validateurs
  *sont* les schémas ; ajouter pydantic = une dépendance pour rien.
- **Restructuration pages/ + src/ (plan §7)** : churn sans valeur
  utilisateur tant que app.py reste lisible ; le plan lui-même
  interdit le « massive change ».
- **Refonte du dashboard (plan §13–14)** : la vue d'équipe suit déjà
  la hiérarchie KPI → alertes → détail.
- **Entrée rapide de tests (plan §15)** : prochain sprint, en entier.
  Design retenu : sélection équipe + test + date → `st.data_editor`
  pré-rempli avec l'effectif du registre → validation par les bornes
  existantes → fusion dans les séances en mémoire → **export du CSV
  séances mis à jour** (cohérent avec l'architecture sans stockage).
