# Épisode 10 · Connexion et rôles

Objectif : protéger l'API. Chaque utilisateur se connecte avec son e-mail et son mot de passe, et chaque route vérifie que son rôle a le droit d'agir. On commence par écrire la matrice des droits, puis on fait générer le code, puis on le fait attaquer.

## 1. D'abord la matrice des droits (sans IA)

Avant tout prompt, on décide qui a le droit de faire quoi, à partir du cahier des charges (section 3). Le résultat est dans [`docs/droits.md`](../docs/droits.md). C'est une décision métier : l'IA l'applique, elle ne l'invente pas.

## 2. Le prompt de génération

```text
Rôle : tu es un expert en sécurité des API, spécialiste de FastAPI et de l'OWASP.
Contexte : API FastAPI + SQLAlchemy + SQL Server (fichiers joints). Six rôles : commercial, vendeur, magasinier, manager, dirigeant, administrateur. La matrice des droits est ci-dessous.
Tâche : ajoute la connexion par e-mail et mot de passe, et le contrôle des droits sur chaque route.
Contraintes :
- mots de passe hachés avec scrypt de la bibliothèque standard, sel aléatoire, paramètres OWASP ; jamais en clair, même dans les logs ;
- jeton JWT signé HS256, valable 30 minutes, qui ne contient que l'identifiant ; le rôle est relu en base à chaque requête ;
- le secret de signature est lu dans le fichier .env ; l'API refuse de démarrer s'il manque ou fait moins de 32 caractères ;
- même message d'erreur que l'e-mail existe ou non, et même durée de calcul ;
- 401 si on ne sait pas qui est l'utilisateur, 403 s'il n'a pas le droit ;
- la matrice des droits dans un seul fichier, et une dépendance autoriser("clients:ecrire") à poser sur chaque route ;
- aucun compte ni mot de passe dans le code ou dans les données de test.
Format : les fichiers complets, puis la liste de ce qui n'est pas couvert.

[coller ici la matrice des droits et les fichiers models.py, schemas.py, main.py et un routeur]
```

## 3. Le prompt d'attaque

On change de rôle : l'IA ne défend plus son code, elle cherche à le casser.

```text
Rôle : tu es un pentesteur. Ton objectif est de contourner la connexion et les droits de cette API.
Contexte : voici le code de la connexion, des jetons et des droits (ci-dessous).
Tâche : liste les attaques possibles, de la plus grave à la moins grave. Pour chacune : comment tu l'essaierais, ce que le code fait aujourd'hui, et le test pytest qui prouve que l'attaque échoue.
Pense au moins à : un jeton modifié à la main, un jeton non signé (alg none), un jeton expiré, un compte désactivé qui garde son jeton, la force brute sur le mot de passe, deviner quels e-mails existent, un administrateur qui se retire ses propres droits.
Format : un tableau attaque / protection / test, puis les tests.

[coller ici securite.py, droits.py, acces.py et routers/auth.py]
```

## 4. La relecture : trois questions

- [ ] **Un mot de passe peut-il être lu ?** En base : seulement l'empreinte scrypt, avec un sel par compte. Dans les réponses de l'API : jamais, ni le mot de passe ni l'empreinte.
- [ ] **Le jeton peut-il être falsifié ?** Il est signé avec un secret du `.env`, pas du code. Un jeton modifié, signé avec un autre secret ou non signé est refusé.
- [ ] **Les erreurs révèlent-elles quelque chose ?** Même message et même durée que le compte existe ou non. `401` : on ne sait pas qui vous êtes. `403` : vous n'avez pas le droit.

## 5. Mettre en route et tester

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # à coller dans .env : JWT_SECRET=...
docker compose up --build
docker compose exec api python -m app.creer_admin admin@votre-entreprise.fr "Prénom Nom"
docker compose exec api pytest
docker compose exec api pytest tests/test_securite.py tests/test_droits.py   # sans base, en une seconde
```
