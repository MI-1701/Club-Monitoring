# Clubs Monitoring — Audit Complet, Architecture & Recommandations

*Document de synthèse globale du projet, analyse architecturale, audit technique et catalogue des prochaines étapes recommandées.*

---

## 1. Synthèse Exécutive

**Clubs Monitoring** est une application web de monitoring de la charge d'entraînement, du bien-être, de la croissance et de la prévention des blessures, conçue spécifiquement pour le volleyball (validée sur le terrain avec les U17 du FUS-VB).

### Points clés :
* **Modèle architectural** : Application Streamlit en mémoire de session (*0 base de données persistante*), protégeant juridiquement le club et le projet vis-à-vis des données de santé de mineures (conformité RGPD / Loi 09-08).
* **Qualité du code** : **69 tests unitaires** (`pytest`) vérifiant l'ensemble des formules et cas limites ; linting propre (`ruff`) ; intégration continue (CI GitHub Actions).
* **Déploiement** : Opérationnel en production sur [club-monitoring.streamlit.app](https://club-monitoring.streamlit.app).
* **Internationalisation** : Bilingue Français / Anglais (interface, alertes et rapports PDF).

---

## 2. Cartographie de l'Architecture & Responsabilités

```
club_monitoring_/
│
├── 🛡️  securite.py            # Garde-fous d'ingestion (taille, lignes, encodage)
├── 🆔 identites.py           # Normalisation des noms, réconciliation & registre
├── 💾 depot.py               # Couche Repository (DepotDonnees / DepotSession)
├── 📊 donnees.py             # Données de démo, modèles CSV, validation métier
├── 🧮 calculs.py             # Moteur scientifique (ACWR, Hooper, Z-scores, etc.)
├── 🌐 i18n.py                # Internationalisation FR / EN & gabarits d'alertes
├── 📄 rapport_pdf.py         # Générateur de rapports PDF (ReportLab + Matplotlib)
├── 🖥️  app.py                 # Interface utilisateur Streamlit (7 vues)
│
├── 🧪 tests/                 # 5 suites de tests automatisés (69 tests verts)
│   ├── test_calculs.py       # 20 tests (charge, ACWR, Hooper, Z-scores, croissance, dispo)
│   ├── test_donnees.py       # 16 tests (validation CSV, bornes, exclusions)
│   ├── test_identites.py     # 8 tests (clés canoniques, accents, arabe, orphelins)
│   ├── test_securite.py      # 8 tests (fichiers volumineux, bombes de lignes, latin-1)
│   └── test_depot.py         # 7 tests (lectures, écriture atomique, export CSV)
│
├── ⚙️  Configuration
│   ├── .github/workflows/    # CI GitHub Actions (ruff + compileall + pytest)
│   ├── .streamlit/           # config.toml (thème, maxUpload 10Mo, XSRF) & secrets.toml.example
│   ├── requirements.txt      # Dépendances de production
│   ├── requirements-dev.txt  # Dépendances de développement (pytest, ruff)
│   └── ruff.toml             # Règles de linting conservatrices
│
└── 📚 Documentation
    ├── README.md             # Présentation générale, installation et capture
    ├── SECURITY.md           # Modèle de sécurité et politique de divulgation
    ├── STORAGE.md            # Justification du stockage en session vs SQL
    ├── PROJET_ETAT.md        # Historique des sprints et état d'avancement
    ├── FICHE_VALIDATION.md   # Grille de smoke tests et protocole de test coach
    └── FICHE_FIVERR.md       # Description du Gig Fiverr prêt au lancement
```

---

## 3. Analyse Détaillée par Composant

### A. Sécurité & Ingestion (`securite.py`)
* **Garde-fous stricts** appliqués **avant** tout chargement en DataFrame Pandas.
* Rejet immédiat des fichiers vides ou excédant **10 Mo** (`TAILLE_MAX_OCTETS`).
* Protection contre les attaques par déni de service / bombes de décompression (limite à **100 000 lignes**).
* Décodage sécurisé en texte (`utf-8-sig` avec repli `latin-1`), sans aucune désérialisation non sécurisée (`pickle`/`eval`).

### B. Réconciliation d'Identité (`identites.py`)
* Résout la fragilité du nom comme clé de jointure entre les 4 CSV.
* `normaliser_cle` : clé canonique insensible à la casse, aux accents (`unicodedata.normalize`), à la ponctuation et aux espaces, tout en préservant les alphabets non latins (ex: arabe).
* Les variantes orthographiques sont regroupées sous la forme la plus fréquente dans la session.
* Détection proactive des orphelins (ex: faute de frappe dans le bien-être) sans jamais fusionner de force des joueuses distinctes ("Sara" vs "Sarah").

### C. Validation & Données (`donnees.py`)
* 4 modules supportés : `seances.csv` (obligatoire), `bien_etre.csv`, `anthropometrie.csv`, `blessures.csv`.
* Neutralisation des valeurs aberrantes (`np.nan` pour RPE $< 1$ ou $> 10$, durée $\le 0$, sauts $< 0$) au lieu de simples messages passifs.
* `valider_saisie_tests` : validation **atomique** de la saisie rapide. S'il reste une seule erreur dans la grille, aucun enregistrement partiel n'a lieu.

### D. Couche Dépôt / Repository (`depot.py`)
* Définit l'interface abstraite `DepotDonnees` et son implémentation en session `DepotSession`.
* Prépare le terrain pour une future implémentation SQL (`DepotPostgres`) sans avoir à réécrire la moindre page Streamlit.
* Gère l'ajout atomique de mesures et l'exportation du CSV séances mis à jour.

### E. Moteur Scientifique (`calculs.py`)
* **Charge d'entraînement** : méthode séance-RPE ($RPE \times Durée$).
* **ACWR (Acute:Chronic Workload Ratio)** : Somme 7 jours (aiguë) / Moyenne hebdo sur 28 jours (chronique). Positionné scientifiquement comme indicateur de vigilance (critique d'Impellizzeri et al. 2020 intégrée).
* **Monotonie & Contrainte (Foster)** : identification des entraînements trop uniformes ($> 2.0$) et pics de contrainte.
* **Indice de Hooper** : Somme quotidienne sommeil + fatigue + courbatures + stress (échelle 4 à 28).
* **Croissance** : Vitesse en cm/an avec fenêtre de lissage $\ge 60$ jours pour éliminer le bruit de mesure. Alerte pic si vitesse $> 7$ cm/an.
* **Disponibilité & Blessures** : Fusion des intervalles qui se chevauchent (`_fusionner_intervalles`) et recadrage strict sur la période d'observation des séances.
* **Alertes individualisées** : Détection par Z-score individuel ($Z > +1.5$ vigilance, $Z > +2.5$ alerte) comparant l'athlète à sa propre référence 28 jours ou historique.

### F. Internationalisation (`i18n.py`)
* Gestion centralisée des dictionnaires bilingues FR / EN.
* Interpolation dynamique des alertes via gabarits paramétrés.
* Sélecteur de langue fluide en haut de la barre latérale.

### G. Rapports PDF (`rapport_pdf.py`)
* Deux rapports complets : Fiche individuelle et Synthèse d'équipe.
* Moteur ReportLab avec graphiques Matplotlib vectoriels exportés à 150 DPI.
* Support bilingue complet transmis depuis l'état de session.

### H. Interface Utilisateur (`app.py`)
* 7 vues spécialisées :
  1. *Vue d'équipe* (KPIs globaux, centre d'alertes fusionné, tableau de synthèse, disponibilité, charge hebdo).
  2. *Fiche joueuse* (Bandeau d'état 360°, progression sur 7 tests, 5 onglets thématiques).
  3. *Saisie rapide* (Grille `st.data_editor` pré-remplie, validation atomique, export CSV direct).
  4. *Bien-être* (Matrice du jour, tendances individuelles, décomposition des 4 items sur 14j).
  5. *Comparaison* (Graphiques multi-athlètes, classement du dernier relevé).
  6. *Rapports PDF* (Génération et téléchargement persistant).
  7. *Méthode* (Documentation scientifique, seuils et références).

---

## 4. Audit & Points d'Attention Identifiés

Bien que le projet soit dans un état très mature, l'audit statique relève quelques axes d'amélioration précis :

### 1. Internationalisation résiduelle dans `app.py`
Quelques chaînes sont restées écrites en français direct sans passer par `t()` :
* `app.py:466` : `st.subheader("Synthese par joueuse")` $\rightarrow$ utiliser `t("synthese_joueuse")`.
* `app.py:484` : `tableau["Bien-etre"]` $\rightarrow$ utiliser `t("col_bien_etre")`.
* `app.py:489` : `st.subheader("Disponibilite")` $\rightarrow$ utiliser `t("disponibilite")`.
* `app.py:492` : `st.caption("Jours d'absence recadres...")` $\rightarrow$ la clé `t("dispo_note")` existe dans `i18n.py` mais n'est pas appelée ici.
* `app.py:498` : `st.subheader("Charge hebdomadaire de l'equipe")` $\rightarrow$ la clé `t("charge_hebdo_equipe")` existe.
* `app.py:514` : `yaxis=dict(title="Charge (unites arbitraires)")` $\rightarrow$ la clé `t("charge_ua")` existe.
* `app.py:800` : `st.selectbox("Indicateur", ...)` $\rightarrow$ utiliser `t("indicateur")`.
* `app.py:892-956` : La page `page_methode()` est rédigée en texte brut français non traduit si la langue active est l'anglais.
* Les graphiques Plotly (`tracer_acwr`, `tracer_hooper`, `tracer_monotonie_contrainte`, `tracer_sauts`, `tracer_croissance`) contiennent des titres et infobulles fixes en français.

### 2. Homogénéité d'usage de la couche Dépôt (`depot.py`)
* Actuellement, seule `page_saisie_rapide` consomme l'instance `depot`. Les autres pages reçoivent encore directement le dictionnaire `donnees`.
* Homogénéiser les appels vers `depot.seances()`, `depot.bien_etre()`, etc. renforcera le découplage en vue d'une future persistance.

### 3. Graphiques & Dossier Images
* Le fichier `README.md` référence des images sous `Pictures/vue_equipe_1.png` etc. Ce dossier n'existe pas localement (des captures d'écran réelles de l'application enrichiront le README et la galerie Fiverr).

---

## 5. Catalogue des Tâches & Prochaines Étapes Proposées

Voici les options de travail structurées par domaine :

```
┌────────────────────────────────────────────────────────────────────────┐
│  AXE 1 : FINITIONS DE CODE & POLISH TECHNIQUE (Immédiat)                │
│  AXE 2 : VALIDATION UTILISATEUR & SMOKE TESTS (Terrain)                │
│  AXE 3 : MARKETING, FIVERR & MISE EN VALEUR DU PRODUIT                 │
│  AXE 4 : ÉVOLUTIONS FONCTIONNELLES FUTURES (Sprint 3)                  │
└────────────────────────────────────────────────────────────────────────┘
```

### AXE 1 — Finitions de code & Polish technique
1. **Nettoyage 100% i18n dans `app.py`** :
   * Remplacer les 7 chaînes hardcodées par leurs équivalents `t(...)`.
   * Internationaliser l'intégralité de la page `page_methode()` en FR/EN.
   * Traduire dynamiquement les titres, axes et infobulles des graphiques Plotly.
2. **Harmonisation de la couche Dépôt** :
   * Passer l'instance `depot` à toutes les pages de `app.py` pour unifier l'accès aux données.
3. **Tests unitaires additionnels pour `i18n.py`** :
   * Ajouter une suite de tests `tests/test_i18n.py` vérifiant que toutes les clés existent dans les deux langues et que les interpolations `{...}` ne lèvent pas d'exception.

### AXE 2 — Validation Utilisateur (Hors-Code / Terrain)
1. **Exécution des 10 Smoke Tests** (`FICHE_VALIDATION.md`) :
   * Tester en ligne sur [club-monitoring.streamlit.app](https://club-monitoring.streamlit.app) les 10 scénarios (import valide, CSV invalide, fichier $> 10$ Mo rejeté, reset de session, génération PDF).
2. **Session de test avec un entraîneur réel** :
   * Donner la consigne : *"Trouvez la joueuse qui nécessite le plus d'attention et expliquez pourquoi"*.
   * Remplir le journal des frictions (P0 à P3).

### AXE 3 — Lancement Commercial & Portfolio
1. **Captures d'écran & Visuels** :
   * Générer des captures d'écran haute résolution de l'application pour créer le dossier `Pictures/`.
2. **Publication du Gig Fiverr** :
   * Utiliser le texte de `FICHE_FIVERR.md` pour publier l'offre de déploiement personnalisé.

### AXE 4 — Sprint 3 : Analytics Longitudinales (Futur)
*(À n'initier qu'après validation utilisateur)*
* Évolution de la charge collective sur plusieurs mois / phases de saison.
* Matrice de corrélation charge / bien-être / performance.
* Historique persistant des alertes et suivi de leur résolution.

---

*Fichier généré pour servir de feuille de route de décision.*
