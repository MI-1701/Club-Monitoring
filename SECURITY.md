# Sécurité

## Modèle de sécurité actuel

Clubs Monitoring est un **démonstrateur sans base de données**. Les
fichiers CSV importés sont traités **en mémoire pendant la session**
puis disparaissent ; l'application ne les persiste dans aucune base.
Ce choix est délibéré : il évite d'héberger des données de santé de
mineures et constitue la principale garantie de confidentialité à ce
stade.

## Ce qui est en place

- **Aucune persistance** : pas de base de données, pas d'écriture
  disque des données importées.
- **HTTPS** fourni par Streamlit Community Cloud.
- **Limite d'upload** : 10 Mo (`.streamlit/config.toml` +
  garde-fou explicite dans `securite.py`), avec contrôle du nombre de
  lignes avant tout traitement.
- **Fichiers traités comme non fiables** : lecture en texte, jamais de
  désérialisation (`pickle`/`eval`) ; validation des colonnes, types,
  bornes et identités avant analyse (`securite.py` → `donnees.py`).
- **Saisie rapide atomique** : un lot de résultats n'est enregistré
  que si **toutes** les valeurs sont valides (pas de fusion partielle).
- **Aucun secret dans le code** : le dépôt ne contient ni clé ni mot de
  passe. `.gitignore` exclut `.env`, `.streamlit/secrets.toml` et les
  répertoires de données réelles.
- **Aucune donnée réelle versionnée** : seules des données de
  démonstration synthétiques sont dans le dépôt.
- **CI** : `ruff` + `pytest` à chaque push.

## Ce qui n'est PAS en place (et pourquoi)

Authentification, autorisation/RBAC, isolation multi-club, journal
d'audit et chiffrement au repos **ne sont pas implémentés**, car il n'y
a ni comptes ni stockage persistant. Les ajouter maintenant reviendrait
à sécuriser une base de données qui n'existe pas. Ils deviennent
nécessaires **le jour où** une vraie persistance multi-utilisateur est
introduite — voir `STORAGE.md`.

## Ne pas faire

- Ne pas déployer de données réelles d'athlètes mineures sur la démo
  publique.
- Ne pas committer de CSV réels ni de secrets.
- Ne jamais prétendre « 100 % sécurisé » ou « aucune donnée stockée »
  sans la nuance « pas de base de données, traitement en session ».

## Signaler une vulnérabilité

Ouvrez une issue GitHub **sans données sensibles**, ou contactez
l'auteur directement pour tout élément confidentiel. Merci de laisser un
délai raisonnable de correction avant toute divulgation publique.
