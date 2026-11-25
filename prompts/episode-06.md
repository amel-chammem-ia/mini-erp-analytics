# Épisode 6 · Architecture et installation

Objectif : poser l'architecture du projet et lancer l'application pour la première fois.

## 1. Le prompt d'architecte

```text
Rôle : tu es un architecte logiciel senior.
Contexte : voici le cahier des charges de Mini-ERP Analytics (ci-dessous). La stack est imposée : interface React (Vite), API Python FastAPI avec SQLAlchemy, base SQL Server 2022, le tout lancé avec Docker Compose.
Tâche : propose l'arborescence du dépôt et écris les fichiers pour un premier lancement : docker-compose.yml, les Dockerfile, une API minimale et une page d'accueil React.
Contraintes :
- aucun secret dans le code : les mots de passe viennent d'un fichier .env, et tu fournis un .env.example ;
- l'API attend que SQL Server soit prêt (contrôle de santé) ;
- une route GET /api/health qui indique si l'API répond et si la base est joignable (503 sinon) ;
- des tests pytest pour cette route, sans base de données réelle.
Format : l'arborescence d'abord, puis chaque fichier en entier, avec son chemin en titre.

[coller ici le contenu de docs/cahier-des-charges.md]
```

## 2. La relecture : les pièges à chercher en priorité

- [ ] **Un mot de passe en clair** dans `docker-compose.yml` ou dans le code → le remplacer par une variable lue dans `.env`.
- [ ] **Une API qui démarre avant la base** → un `healthcheck` sur SQL Server et `depends_on: condition: service_healthy`.
- [ ] **Un `.env` envoyé sur GitHub** → vérifier qu'il est bien dans `.gitignore`.
- [ ] **Des versions non maîtrisées** → bornes de version dans `requirements.txt` et `package.json`.
- [ ] **Des tests qui exigent une vraie base** → simuler la base dans les tests.

## 3. Le premier lancement

```bash
cp .env.example .env          # puis changez le mot de passe
docker compose up --build     # lance db, api et web
```

- Interface : http://localhost:5173 (affiche « API : En ligne » et « Base de données : Connectée »)
- API : http://localhost:8000/api/health
- Documentation de l'API : http://localhost:8000/docs

```bash
docker compose exec api pytest    # 2 tests
```

## 4. L'intégration

```bash
git add .
git commit -m "Architecture : conteneurs Docker et route de santé"
git push
```
