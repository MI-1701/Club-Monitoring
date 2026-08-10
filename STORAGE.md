# Architecture de stockage — état actuel et évolution

## Aujourd'hui : session, sans base de données

Toutes les données vivent en mémoire pendant la session Streamlit. Le
seul point de passage entre l'interface et les données est la couche
**dépôt** (`depot.py`) :

```
     Interface (app.py)
            │
            ▼
   DepotDonnees (interface)
            │
            ▼
   DepotSession  ← DataFrames en mémoire (actuel)
```

`DepotSession` enveloppe le dictionnaire `donnees` (seances,
bien_etre, anthropometrie, blessures, registre). Aucune écriture disque.

## Pourquoi PostgreSQL n'est PAS branché maintenant

C'est un choix, pas un oubli. Brancher une base impliquerait de
**conserver de façon persistante des données de santé identifiées de
mineures**, ce qui déclenche immédiatement des obligations que le
produit actuel évite :

- authentification et gestion de comptes ;
- autorisation / RBAC et isolation entre clubs ;
- chiffrement au repos, sauvegardes, politique de rétention et de
  suppression ;
- conformité (Loi 09-08 au Maroc, RGPD dès qu'un club français importe
  des données).

Tant qu'il n'y a **ni second utilisateur réel, ni besoin de conserver
les données entre sessions**, la version sans stockage est à la fois
plus simple et plus sûre — et « aucune donnée persistée » reste un
argument commercial et un bouclier juridique.

De plus, Streamlit Community Cloud n'offre **ni base ni disque
persistant** : un SQLite serait effacé à chaque redéploiement, et
Postgres nécessiterait un hébergeur externe (Supabase, Neon, Render)
avec une chaîne de connexion dans les secrets. « Introduire Postgres »
signifie donc changer d'hébergement et de nature de produit, pas
seulement ajouter du code.

## Quand l'introduire

Lorsque **tous** ces besoins sont réels (pas hypothétiques) :

```
plusieurs clubs → plusieurs entraîneurs → comptes → authentification
→ RBAC → données d'athlètes persistantes → base → audit → isolation
```

À ce moment-là seulement :

```
     Interface (app.py)  ← inchangée
            │
            ▼
   DepotDonnees (interface)  ← inchangée
            │
            ▼
   DepotPostgres  ← nouvelle implémentation SQL
```

## Comment migrer (le jour venu)

1. Choisir un hébergeur avec base managée (Render + Postgres, ou
   Supabase/Neon) ; mettre la chaîne de connexion dans
   `.streamlit/secrets.toml` (jamais dans le code).
2. Écrire `DepotPostgres(DepotDonnees)` : mêmes méthodes
   (`seances()`, `ajouter_mesures_tests()`, …) adossées à des requêtes
   SQL. L'esquisse commentée est déjà en bas de `depot.py`.
3. Ajouter authentification + RBAC **dans le même sprint** — ne jamais
   livrer la persistance de données de mineures sans contrôle d'accès.
4. Aucune page Streamlit ne change : elles ne parlent qu'à l'interface
   `DepotDonnees`.

C'est précisément ce que la couche dépôt rend possible : la base
pourra être introduite **sans réécrire l'application**.
