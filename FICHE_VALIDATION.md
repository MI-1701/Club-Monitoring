# Clubs Monitoring — Fiche de validation

*À remplir en testant l'application en ligne
(https://club-monitoring.streamlit.app) puis en observant un coach.*

**Date du test :** ______________  **Testeur :** ______________
**Version / commit :** ______________

---

## Phase 1 — Smoke tests (à faire soi-même, ~20 min)

Cocher `[x]` si le résultat attendu est obtenu. Noter tout écart.

### 1. L'application démarre
- [ ] La page charge, le tableau « Vue d'equipe » apparaît.
- [ ] Aucun traceback Python, aucune page blanche, aucun
      `ModuleNotFoundError`.
- **Écart observé :** ______________________________________________

### 2. Mode démonstration
- [ ] Les données fictives peuplent le dashboard (8 joueuses).
- [ ] Le bandeau « Données de demonstration » est visible.
- **Écart :** ______________________________________________________

### 3. Import CSV valide
- [ ] Bascule sur « Importer mes fichiers CSV », import du modèle
      séances → les joueuses apparaissent, message de succès.
- [ ] Aucune perte silencieuse (le nombre de joueuses correspond).
- **Écart :** ______________________________________________________

### 4. CSV invalide rejeté
- [ ] Import d'un CSV sans colonne obligatoire → message clair du type
      « Colonne obligatoire manquante : … ».
- [ ] Aucun traceback affiché à l'utilisateur.
- **Écart :** ______________________________________________________

### 5. Fichier trop volumineux rejeté  *(test que je n'ai pas pu faire)*
- [ ] Import d'un fichier > 10 Mo → rejet avec message
      « Fichier trop volumineux … Limite : 10 Mo ».
- [ ] Le rejet a lieu **avant** tout traitement.
- **Écart :** ______________________________________________________
- *Astuce : dupliquer des lignes d'un CSV jusqu'à dépasser 10 Mo, ou
  renommer un gros fichier quelconque en .csv.*

### 6. Réconciliation d'identité
- [ ] CSV avec « Salma B. », « salma b », « Sàlma-B » → regroupés,
      message « Noms regroupes sous … » dans la barre latérale.
- [ ] « Sara » et « Sarah » restent distinctes (non fusionnées).
- [ ] Un nom du bien-être sans correspondance → avertissement orphelin.
- **Écart :** ______________________________________________________

### 7. Saisie rapide
- [ ] Page « Saisie rapide » → choix test + date → grille pré-remplie
      avec l'effectif.
- [ ] Saisir une valeur aberrante (ex. CMJ = 250) → l'export est
      **bloqué**, la joueuse fautive est nommée.
- [ ] Compteur « ✓ X/Y valides » cohérent.
- **Écart :** ______________________________________________________

### 8. Export d'une saisie valide
- [ ] Saisie valide → aperçu → confirmer → « X résultat(s) ajouté(s) ».
- [ ] La nouvelle valeur apparaît immédiatement dans la fiche joueuse.
- [ ] Téléchargement du CSV mis à jour.
- [ ] **Aller-retour** : ré-importer ce CSV → mêmes données, aucun rejet.
- **Écart :** ______________________________________________________

### 9. Génération PDF
- [ ] Page « Rapports PDF » → fiche individuelle → le PDF s'ouvre.
- [ ] Bon nom de club, bonnes dates, pas de caractères cassés, pas
      d'info de debug.
- [ ] Le bouton de téléchargement reste après un premier clic.
- **Écart :** ______________________________________________________

### 10. Reset de session  *(test que je n'ai pas pu faire)*
- [ ] Après un import, rebasculer sur « Données de demonstration » →
      les données importées disparaissent partout (tableau, fiches,
      alertes).
- **Écart :** ______________________________________________________

**Bilan Phase 1 :** ____ / 10 réussis.
Blocages (P0) éventuels : ___________________________________________

---

## Phase 2 — Test coach réel

### Protocole
Donner **une** tâche, sans expliquer les clics, et observer en silence :

> « Trouvez la joueuse qui nécessite le plus d'attention et
> expliquez-moi pourquoi. »

Noter : où hésite-t-il ? Que clique-t-il ? Que comprend-il de travers ?
Qu'attendait-il ? Qu'ignore-t-il ? Que demande-t-il ?

### Journal de friction

| Problème observé | Sévérité | Fréquence | Solution proposée | Statut |
|---|---|---|---|---|
|  |  | /1 |  | Ouvert |
|  |  | /1 |  | Ouvert |
|  |  | /1 |  | Ouvert |
|  |  | /1 |  | Ouvert |

Sévérité : **P0** bloque la tâche · **P1** friction majeure ·
**P2** friction notable · **P3** cosmétique.

### Questions au coach (après la tâche)
1. Quelle action vous a semblé la plus difficile ?
   ________________________________________________________________
2. Quelle information n'était pas assez claire ?
   ________________________________________________________________
3. Quelle étape vous ferait gagner le plus de temps ?
   ________________________________________________________________
4. Quel indicateur ou quelle alerte est difficile à interpréter ?
   ________________________________________________________________
5. Quelle information vous manque pour décider d'un entraînement ?
   ________________________________________________________________
6. Sur 10, la facilité d'utilisation : ____ / 10

---

## Phase 3 — Décider la suite (après Phases 1 et 2)

- Corriger d'abord les frictions **P0/P1** (ce sont elles qui reviennent
  et qui bloquent la tâche). C'est le prochain vrai sprint de code, piloté
  par les preuves ci-dessus — pas par un plan théorique.
- **Sprint 3 (analytics longitudinales)** seulement après ces corrections.
- **Persistance / base / auth** seulement si le coach demande
  explicitement plusieurs comptes, plusieurs clubs, ou des données
  conservées entre sessions.

---

## Rappel — priorité hors validation

Le produit est **déployé et démontrable**. La démo en ligne est
exactement l'élément que la prestation Fiverr attend. Publier la
prestation en pointant vers `club-monitoring.streamlit.app` a plus de
valeur immédiate que n'importe quelle correction cosmétique.
