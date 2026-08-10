# Sprint 1 — Correctness & crédibilité (roadmap §4, 9, 10, 11, 23, 53, 57, 58, 62)

## Bug corrigé (le seul vrai bug trouvé)

**`calculer_disponibilite` (calculs.py)** — roadmap §11. Les jours
d'absence étaient simplement additionnés : deux blessures qui se
chevauchent (1–10 mars + 5–15 mars) comptaient 21 jours au lieu de 15.
Correction : construction d'intervalles `[début, début + jours - 1]`,
fusion des chevauchements, recadrage sur la période des séances (les
jours hors période ne pénalisent plus la disponibilité). Vérifié par
4 tests dédiés. Les valeurs de la démo sont inchangées (aucun
chevauchement dans le jeu de démo).

## Validation renforcée (donnees.py) — roadmap §9, §10

- RPE hors 1–10, durée ≤ 0, sauts < 0 : mis à NaN (exclus des calculs)
  avec avertissement, au lieu d'un simple avertissement sans effet.
- Bien-être hors échelle 1–7 : la ligne est réellement exclue.
- Dates futures : avertissement (sans rejet — les modèles CSV
  d'exemple sont datés de la saison à venir).
- Détection des variantes de noms (« Salma B. » vs « salma b. ») qui
  créeraient des joueuses fantômes — avertissement explicite.

## Langage scientifique (calculs.py, app.py, rapport_pdf.py, README) — §23, §53

L'ACWR n'est plus présenté comme prédicteur de blessure :
- Étiquettes : « Zone optimale » → « Zone habituelle » ;
  « Risque élevé » → « Hausse forte — vigilance accrue » ;
  « Sous-charge » → « Charge en baisse marquée ».
- Page Méthode et PDF : mention explicite de la critique
  d'Impellizzeri et al. (2020) ; l'ACWR = signal de variation de
  charge, pas une prédiction. Défendable en soutenance.

## Corrections UX (app.py)

- Le bouton de téléchargement PDF disparaissait après le premier clic
  (anti-pattern Streamlit : `download_button` dans le bloc `if button`).
  Les octets du PDF sont maintenant conservés en `session_state`.
- Le titre de l'onglet navigateur affichait « FUS-VB — Monitoring » au
  premier chargement (défaut résiduel) → « CLUB — Monitoring ».
  Idem pour les défauts `nom_club` de rapport_pdf.py.
- Légende sous le tableau de disponibilité expliquant la fusion des
  épisodes.

## Tests + CI — §57, §58

- `tests/test_calculs.py` + `tests/test_donnees.py` : 33 tests, tous
  verts. Chaque indicateur est vérifié sur un cas dont le résultat est
  calculable à la main (ex. ACWR constant = 1,0 ; pic 21×100 + 7×200
  → 1,6 ; exemple de chevauchement du §11 → 15 jours).
- `.github/workflows/ci.yml` : ruff + compileall + pytest à chaque
  push. Badge ajouté au README.
- `ruff.toml` : règles conservatrices (E4/E7/E9/F) — erreurs réelles
  uniquement, pas de refonte stylistique imposée.
- 4 imports inutilisés supprimés (numpy dans app.py et rapport_pdf.py,
  interpreter_hooper, Spacer).
- `conftest.py` vide à la racine (nécessaire aux imports des tests).

## README — §62

Typo « > > » corrigée, badge CI, section « Qualité du code », section
« Confidentialité » (traitement en session, aucune donnée stockée —
argument commercial réel pour des données de mineures), structure mise
à jour.

## Non fait, volontairement

Authentification, base de données, RBAC, refonte multi-pages : voir la
discussion — ces phases changent la nature du produit (service hébergé
avec données persistantes de mineures) et ne servent ni la thèse ni le
Fiverr à court terme.
