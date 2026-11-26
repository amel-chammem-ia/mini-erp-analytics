# Mini-ERP Analytics

> Un vrai logiciel de gestion construit **en écrivant le code avec des prompts**.
> Projet fil rouge de la saison 2 de la chaîne YouTube **Formation Prompt Engineering** (Amel Chammem, Formation IA & Data).

Mini-ERP Analytics est un ERP simple pour une petite entreprise : on y gère les **clients**, les **produits**, les **ventes** et le **stock**, puis on analyse les données dans des **tableaux de bord partageables** avec l'équipe.

Chaque épisode ajoute une brique au projet. Ce dépôt contient, épisode par épisode :

- le **code** de l'application ;
- les **prompts** utilisés pour le générer (dossier [`prompts/`](prompts/)) ;
- la **documentation** du projet (dossier [`docs/`](docs/)).

## La stack

| Couche | Technologie |
|---|---|
| Interface | React |
| API | Python · FastAPI |
| Base de données | SQL Server |
| Déploiement | Docker |

## Démarrage rapide

Prérequis : [Docker Desktop](https://www.docker.com/products/docker-desktop/) et Git.

```bash
git clone https://github.com/amel-chammem-ia/mini-erp-analytics.git
cd mini-erp-analytics
cp .env.example .env          # puis changez le mot de passe et ajoutez JWT_SECRET dans .env
docker compose up --build
docker compose exec api python -m app.creer_admin admin@votre-entreprise.fr "Prénom Nom"
```

- Interface : http://localhost:5173
- API : http://localhost:8000/api/health (documentation : http://localhost:8000/docs)
- Tests de l'API : `docker compose exec api pytest`

Le premier lancement télécharge les images (celle de SQL Server dépasse 1 Go) : comptez quelques minutes. Au démarrage, le service `db-init` crée la base `MiniERP` et charge des données de test fictives. L'architecture est décrite dans [`docs/architecture.md`](docs/architecture.md), la base dans [`docs/base-de-donnees.md`](docs/base-de-donnees.md), l'API dans [`docs/api.md`](docs/api.md), la méthode de test et de débogage dans [`docs/debogage.md`](docs/debogage.md), la connexion et les droits par rôle dans [`docs/droits.md`](docs/droits.md), les ventes et les factures dans [`docs/factures.md`](docs/factures.md).

## La méthode : le cycle du développeur prompt engineer

1. **Spécifier** : décrire précisément une seule petite tâche.
2. **Générer** : écrire un prompt qui donne le contexte du projet (rôle, contexte, tâche, contraintes, format).
3. **Vérifier** : lire le code et lancer les tests.
4. **Intégrer** : faire un commit propre dans Git. Puis passer à la tâche suivante.

L'IA écrit vite. Vous restez l'architecte et le garant de la qualité.

## Le programme (épisodes 5 à 20)

| Épisode | Thème | Prompts |
|---|---|---|
| 5 | [Devenir développeur prompt engineer](https://youtu.be/T5o0Q5thRhg) · le cahier des charges | [`prompts/episode-05.md`](prompts/episode-05.md) |
| 6 | [Architecture et premier lancement](https://youtu.be/XuGk4WG5dMw) · Docker Compose | [`prompts/episode-06.md`](prompts/episode-06.md) |
| 7 | [La base SQL Server](https://youtu.be/mx3sTFkMawc) · tables, contraintes, données de test | [`prompts/episode-07.md`](prompts/episode-07.md) |
| 8 | [L'API clients et produits](https://youtu.be/8yY8ea7g_sE) · FastAPI, validation, codes d'erreur | [`prompts/episode-08.md`](prompts/episode-08.md) |
| 9 | [Tests et débogage](https://youtu.be/hwKSpsUV6Wo) · un vrai bug de fuseau horaire corrigé | [`prompts/episode-09.md`](prompts/episode-09.md) |
| 10 | [Connexion et rôles](https://youtu.be/mL-6Pc3gjxY) · mots de passe hachés, jeton signé, droits par rôle | [`prompts/episode-10.md`](prompts/episode-10.md) |
| 11 | [Ventes et factures](https://youtu.be/FgNGGHJ_h7s) · totaux au centime, numéro de facture, facture PDF | [`prompts/episode-11.md`](prompts/episode-11.md) |
| 12 | Stock et alertes | à venir |
| 13 | L'interface React | à venir |
| 14 | Les écrans métier | à venir |
| 15 | Les analyses SQL | à venir |
| 16 | Tableaux de bord | à venir |
| 17 | Partage des analyses | à venir |
| 18 | Qualité et revue de code | à venir |
| 19 | Mise en production | à venir |
| 20 | Examen final et certification | à venir |

Le détail est dans [`docs/roadmap.md`](docs/roadmap.md) et le cahier des charges dans [`docs/cahier-des-charges.md`](docs/cahier-des-charges.md).

## Suivre le projet

- Chaîne YouTube : [@FormationPromptEngineering](https://www.youtube.com/@FormationPromptEngineering)
- Playlist : « Formation Prompt Engineering »
- Mettez une ⭐ au dépôt pour être averti des nouveaux épisodes.

---

### English summary

Mini-ERP Analytics is a small ERP (customers, products, sales, stock, shareable analytics dashboards) built step by step **by writing the code with prompts**, as the season 2 project of the YouTube course *Formation Prompt Engineering* (narrated in French, English subtitles available). Stack: React, Python FastAPI, SQL Server, Docker. Each episode adds the code and the exact prompts used to generate it.
