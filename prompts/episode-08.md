# Épisode 8 · L'API clients et produits

Objectif : écrire les routes FastAPI qui permettent à l'interface de rechercher, lire, créer, modifier et supprimer les clients et les produits.

## 1. Le prompt d'expert API

```text
Rôle : tu es un développeur back-end senior, expert FastAPI, Pydantic v2 et SQLAlchemy 2.
Contexte : projet Mini-ERP Analytics. Voici les modèles SQLAlchemy (backend/app/models.py) et le cahier des charges (ci-dessous). La session de base de données est fournie par la dépendance get_session de backend/app/database.py.
Tâche : écris les routes CRUD de /api/clients et /api/produits.
Contraintes :
- des schémas Pydantic séparés pour la création, la modification (PATCH partiel) et la lecture ;
- chaque champ validé : e-mail, numéro de TVA, prix positif avec 2 décimales, TVA entre 0 et 100 ; champs inconnus refusés ;
- recherche par nom, e-mail ou ville, paginée par 20 ;
- codes HTTP précis : 201 à la création, 404 si introuvable, 409 en cas de doublon, 422 si la donnée est invalide ;
- un client qui a des ventes ne se supprime pas ; un produit s'archive au lieu d'être supprimé ;
- le stock ne se saisit pas par l'API ;
- des tests pytest pour chaque règle, sur une base SQLite en mémoire.
Format : un fichier par routeur, les schémas dans schemas.py, puis un tableau des routes avec leurs codes de réponse.

[coller ici backend/app/models.py et docs/cahier-des-charges.md]
```

## 2. La relecture : trois questions

- [ ] **Les entrées sont-elles validées ?** Un prix négatif, un e-mail mal formé ou un champ inconnu (`"stock_actuel": 50`) doivent être refusés avec un code `422`, avant d'atteindre la base.
- [ ] **Chaque erreur a-t-elle le bon code ?** `404` si la ressource n'existe pas, `409` en cas de doublon, jamais un `500` ni un `200` avec un message d'erreur.
- [ ] **Que se passe-t-il quand on supprime ?** Un client qui a des ventes reste en base ; un produit déjà vendu s'archive. Les factures doivent rester lisibles.

Piège fréquent : la recherche construite avec `LIKE '%' + saisie + '%'` sans échapper `%` et `_`. Chercher « 100% » renvoie alors tous les clients dont le nom contient « 100 ».

## 3. Le test dans le navigateur

```bash
docker compose up --build
```

Ouvrez http://localhost:8000/docs : FastAPI a généré la documentation interactive. Pour chaque route : **Try it out**, puis **Execute**.

1. `POST /api/clients` avec un nouveau client : réponse `201`.
2. Le même appel une seconde fois : réponse `409`.
3. `GET /api/clients?recherche=lyon` : les clients lyonnais, par pages de 20.

## 4. Les tests automatiques

```bash
docker compose exec api pytest
```

Les tests de l'API tournent sur une base SQLite en mémoire : ils ne touchent jamais aux données de SQL Server.

Le détail des routes et des règles est dans [`docs/api.md`](../docs/api.md).
