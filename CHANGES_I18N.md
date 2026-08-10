# Sprint i18n — Interface bilingue FR / EN

## Objectif
Un sélecteur de langue dans la barre latérale qui bascule **toute**
l'application entre français et anglais : interface, alertes ET rapports
PDF.

## Nouveau module : `i18n.py`
- Source unique de tout le texte visible : `t("cle")` renvoie la version
  dans la langue courante (stockée en session, `st.session_state`).
- ~130 chaînes d'interface + 7 gabarits d'alerte + étiquettes ACWR, toutes
  bilingues.
- Les alertes dynamiques utilisent des gabarits `str.format` : les
  nombres (« Z = +4.4 », « ACWR 1.48 ») s'interpolent identiquement dans
  les deux langues.
- Ajouter une langue = une colonne de plus. Ajouter une chaîne = une
  entrée `{cle: {"fr": ..., "en": ...}}`.

## Architecture
- **Sélecteur de langue** en tête de la barre latérale ; toute la session
  se réaffiche dans la langue choisie.
- **`calculs.py`** : les alertes portent désormais une `cle` + des
  `params` structurés (le `message` français est conservé comme repli,
  ce qui garde les 69 tests verts). Nouveau `cle_acwr()` qui renvoie une
  clé d'étiquette traduisible.
- **Navigation** : les valeurs internes des pages restent en français
  (le routage ne casse pas) ; seul l'affichage est traduit via
  `format_func`.
- **`rapport_pdf.py`** : les deux rapports prennent un paramètre
  `lang="fr"` ; table `PDF_TEXTES` couvrant les 17 libellés, le
  paragraphe de méthode et les étiquettes ACWR. L'app transmet la langue
  courante.

## Vérifications
- 69 tests toujours verts (la couche i18n est additive).
- ruff propre, compileall OK.
- Les 4 PDF (fiche + équipe × FR + EN) se génèrent sans erreur ; texte
  extrait et vérifié : « Team report / Load alerts / Watch » en EN vs
  « Rapport d'equipe / Alertes de charge / Vigilance » en FR.
- Audit statique : **aucune clé `t()` manquante** ; toutes les entrées
  sont bien bilingues. Même une clé manquante retomberait sur la clé
  elle-même (jamais de crash).

## À vérifier en ligne (impossible hors navigateur)
1. Basculer la langue et parcourir chaque page : aucun libellé brut
   (ex. `page_saisie`) ne doit apparaître.
2. Générer les deux PDF en anglais et les ouvrir : libellés traduits,
   mise en page intacte.

## Reste en français (choix)
Les commentaires de code et les 3 changelogs de sprint restent en
français (documentation interne, pas vue par l'utilisateur final).
