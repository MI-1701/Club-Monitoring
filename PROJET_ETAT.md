# Clubs Monitoring — État du projet

*Récapitulatif de tout ce qui a été construit, du point de départ à aujourd'hui.*

**Auteur :** Ilias Moudrikah
**Dépôt :** https://github.com/MI-1701/Club-Monitoring (public)
**Démo en ligne :** https://club-monitoring.streamlit.app
**État :** déployé, 69 tests verts, ruff propre. Phase de code terminée ;
phase de validation utilisateur en cours.

---

## 1. Résumé en une phrase

Un tableau de bord Streamlit de monitoring physique pour le volleyball
(charge, bien-être, sauts, croissance, blessures, alertes
individualisées), passé d'un prototype étudiant à **un produit déployé,
testé et défendable** — sans base de données, sans authentification,
volontairement, tant qu'un vrai besoin multi-utilisateur n'existe pas.

---

## 2. Point de départ

Application fonctionnelle mais fragile : ~7,5/10.

- 4 fichiers source (`app.py`, `calculs.py`, `donnees.py`,
  `rapport_pdf.py`), aucun test, aucune CI.
- Un vrai bug de calcul (disponibilité).
- Langage scientifique trop affirmatif sur l'ACWR.
- Un défaut de marque résiduel (« FUS-VB » codé en dur).
- Identité des joueuses fragile entre fichiers.

---

## 3. Sprint 1 — Correction & crédibilité scientifique

**Objectif : fiabilité et défendabilité avant toute nouvelle
fonctionnalité.**

- **Bug corrigé — disponibilité.** Les jours d'absence étaient
  additionnés bêtement : deux blessures qui se chevauchent (1–10 +
  5–15 mars) comptaient 21 jours au lieu de 15. Correction par fusion
  d'intervalles + recadrage sur la période observée.
- **Validation renforcée.** RPE hors 1–10, durée ≤ 0, sauts < 0,
  bien-être hors 1–7 : réellement exclus des calculs (avant : simple
  avertissement sans effet). Dates futures signalées. Variantes de noms
  détectées.
- **Langage ACWR assaini.** « Zone optimale » → « Zone habituelle » ;
  « Risque élevé » → « Hausse forte — vigilance accrue ». Mention
  explicite de la critique d'Impellizzeri (2020). Défendable en
  soutenance.
- **Corrections UX.** Bouton de téléchargement PDF qui disparaissait
  (anti-pattern Streamlit) ; titre d'onglet « FUS-VB » résiduel.
- **Tests + CI créés.** Suite `pytest`, GitHub Actions (ruff + pytest),
  `ruff.toml`, badge CI. Point de bascule « script étudiant » →
  « outil ingénieré ».

---

## 4. Sprint 1.5 — Identité des joueuses + vue 360

**Objectif du plan « Next Move » : modèle de données propre, sans
alourdir les CSV du coach.**

- **Nouveau module `identites.py`.** Clé canonique insensible à la
  casse, aux accents, à la ponctuation, aux espaces (alphabets non
  latins préservés). « Salma B. », « salma b », « Sàlma-B » → même
  joueuse.
- **Harmonisation entre les 4 fichiers.** Avant : un bien-être saisi
  « salma b. » était **silencieusement invisible** sur la fiche de
  « Salma B. » — vraie perte de données. Corrigé. Noms sans
  correspondance signalés (orphelins) ; noms proches jamais fusionnés
  automatiquement (« Sara » ≠ « Sarah »).
- **Identifiants internes** ATH-001… par session, prêts pour la saisie
  rapide et les exports, sans charge pour l'utilisateur.
- **Vue 360 sur la fiche joueuse.** Bandeau d'état instantané (ACWR,
  Hooper du jour, disponibilité, alertes actives) avant tout onglet.
- **Refactor.** Fusion des alertes ACWR + individualisées déplacée dans
  la couche calculs (`construire_toutes_alertes`), réutilisée partout.

---

## 5. Sprint 2 — Sécurité, saisie rapide & couche dépôt

**Objectif : version déployable et réellement utilisable par un coach.**

### Sécurité
- **`securite.py`** : garde-fous taille (10 Mo), fichier vide, bombe de
  lignes (> 100 000), encodage utf-8/latin-1 — **avant** tout parsing.
  Aucune désérialisation (pas de pickle).
- **`.streamlit/config.toml`** : `maxUploadSize = 10`, XSRF, télémétrie
  désactivée.
- **`.gitignore` durci** : `.env`, secrets, `data/private/`,
  `data/real/`, `*_reel.csv` — données réelles et secrets non
  committables par accident.
- **`SECURITY.md`**, **`.streamlit/secrets.toml.example`**, expander
  « Confidentialité & sécurité » in-app avec la formulation exacte
  (« traitées en mémoire… ne les persiste dans aucune base »).

### Saisie rapide
- **Nouvelle page.** Un test pour toute l'équipe via `st.data_editor`
  pré-rempli depuis le registre.
- **Validation atomique** (`valider_saisie_tests`) : bornes de
  plausibilité par test ; s'il reste **une** erreur, rien n'est
  enregistré (pas de fusion partielle). Cellule vide = non testée,
  ignorée. Virgule décimale acceptée.
- **Flux** éditer → valider tout → aperçu → confirmer → ajout en
  mémoire → **export du CSV mis à jour** (re-importable). Les nouvelles
  valeurs apparaissent immédiatement dans les fiches et alertes.

### Couche dépôt (décision d'architecture)
- **`depot.py`** : interface unique `DepotDonnees` entre l'UI et les
  données. Aujourd'hui `DepotSession` (DataFrames en mémoire) ; esquisse
  `DepotPostgres` commentée pour plus tard.
- **PostgreSQL / auth / RBAC volontairement reportés.** Raison
  documentée dans `STORAGE.md` : brancher une base = héberger des
  données de santé de mineures = auth, RBAC, chiffrement, rétention,
  conformité (Loi 09-08 / RGPD). À faire seulement avec un vrai besoin
  multi-utilisateur. « Aucune donnée persistée » reste un argument
  commercial et un bouclier juridique.

---

## 6. Déploiement

- Poussé sur GitHub (dépôt public, propre, données synthétiques
  uniquement).
- Déployé sur Streamlit Community Cloud, HTTPS,
  `club-monitoring.streamlit.app`.
- Python fixé à une version avec wheels disponibles (évite les échecs
  de build sur 3.14).
- Application vérifiée en ligne : nav « Saisie rapide » présente,
  expander confidentialité présent, centre d'alertes fonctionnel sur la
  démo (la surcharge programmée de la Joueuse 5 se déclenche
  correctement).

---

## 7. État technique actuel

| Élément | État |
|---|---|
| Modules source | `app.py`, `calculs.py`, `donnees.py`, `identites.py`, `securite.py`, `depot.py`, `rapport_pdf.py` |
| Tests | **69**, tous verts |
| Fichiers de test | `test_calculs`, `test_donnees`, `test_identites`, `test_securite`, `test_depot` |
| Lint | ruff propre |
| CI | GitHub Actions (ruff + pytest) |
| Déploiement | Streamlit Community Cloud, en ligne |
| Docs | README, SECURITY.md, STORAGE.md, 3 changelogs de sprint |
| Stockage | Session uniquement, aucune base |

---

## 8. Ce qui reste — et ce n'est PAS du code

Le dernier roadmap le dit lui-même : la priorité immédiate n'est **pas**
un nouveau sprint de code, mais la **validation par un vrai
utilisateur**.

### À faire par Ilias (pas automatisable)
1. **Smoke test sur l'app en ligne** (~15 min) : démarrage, mode démo,
   import CSV valide/invalide, **fichier > 10 Mo rejeté**, **reset de
   session vide bien les données**, saisie rapide, valeur aberrante qui
   bloque l'export, PDF.
2. **Test coach réel** : donner la tâche « trouvez la joueuse qui
   nécessite le plus d'attention et expliquez pourquoi », observer sans
   guider, noter les frictions (tableau P0–P3).
3. **Fiverr** : publier la prestation en pointant vers la démo en ligne.

### Petits restes cosmétiques
- Remplacer le README par la version corrigée (badge + formulation
  confidentialité).
- Vérifier que l'onglet Actions affiche un run CI vert.

### Sprint 3 — plus tard, seulement après validation
Analytics longitudinales (évolution CMJ/charge/bien-être dans le temps,
persistance des alertes, vue équipe dans le temps). **À ne pas commencer
avant** le smoke test, le test coach et les premières frictions
corrigées.

### Décision d'architecture — encore plus tard
« Avons-nous réellement besoin d'une persistance multi-utilisateur ? »
À trancher sur preuves (plusieurs coachs, plusieurs clubs, données à
conserver entre sessions), pas par principe. La couche dépôt rend cette
bascule possible sans réécrire l'application.

---

## 9. Principe directeur

```text
CORRECT → SÉCURISÉ → UTILISABLE → UTILE → MESURABLEMENT UTILE → SCALABLE
```

Les étapes CORRECT, SÉCURISÉ et UTILISABLE sont faites. La suite
(UTILE, prouvé par un vrai coach) ne se code pas : elle s'observe.
