# Épisode 7 · La base SQL Server

Objectif : créer la base de Mini-ERP Analytics, avec ses règles, et la remplir de données de test réalistes.

## 1. Le prompt d'expert en bases de données

```text
Rôle : tu es un expert SQL Server et en modélisation de données.
Contexte : voici le cahier des charges de Mini-ERP Analytics (ci-dessous). Base : SQL Server 2022, schéma dbo, noms de tables et de colonnes en français, en minuscules avec des underscores.
Tâche : écris le script T-SQL qui crée la base MiniERP et les tables clients, produits, ventes, lignes_vente et mouvements_stock.
Contraintes :
- clés primaires, clés étrangères et contraintes nommées ;
- montants en DECIMAL, jamais en FLOAT ;
- contrôles CHECK pour les règles métier (quantités > 0, statut de vente autorisé, TVA entre 0 et 100) ;
- e-mail et numéro de TVA des clients uniques ;
- index sur les colonnes filtrées ou jointes souvent ;
- un script relançable sans erreur (IF ... IS NULL avant chaque création).
Format : le script complet, puis un tableau qui justifie chaque contrainte et chaque index.

[coller ici le contenu de docs/cahier-des-charges.md]
```

## 2. La relecture : trois questions

- [ ] **Les montants sont-ils en `DECIMAL` ?** `FLOAT` stocke une valeur approchée : les centimes finissent par s'arrondir de travers.
- [ ] **Les règles métier sont-elles dans la base ?** Quantité positive, e-mail unique, statut autorisé : des contraintes `CHECK` et `UNIQUE`.
- [ ] **Les colonnes filtrées souvent ont-elles un index ?** Date de vente, client, produit.

## 3. Le prompt des données de test

```text
Écris le script T-SQL 02_seed.sql qui remplit la base MiniERP avec des données de test réalistes :
- 8 entreprises clientes fictives (adresses e-mail en .example, numéros de TVA fictifs) ;
- 10 produits informatiques avec des prix réalistes ;
- 14 ventes réparties d'août à novembre 2026, dont une annulée et une en brouillon ;
- des mouvements de stock cohérents : le stock actuel de chaque produit est égal à la somme de ses mouvements.
Le script ne fait rien si des clients existent déjà, et tout est dans une transaction.
```

Règle d'or : jamais de vraies données clients dans un dépôt public.

## 4. Le lancement

Le service `db-init` de `docker-compose.yml` attend SQL Server, exécute `database/01_schema.sql` puis `database/02_seed.sql`, et l'API ne démarre qu'après.

```bash
docker compose up --build
```

Vérification, depuis votre outil SQL (serveur `localhost,1433`) :

```sql
-- database/requetes/ca_par_mois.sql
SELECT FORMAT(date_vente, 'yyyy-MM') AS mois, SUM(total_ht) AS ca_ht
FROM dbo.ventes
WHERE statut = N'validee'
GROUP BY FORMAT(date_vente, 'yyyy-MM')
ORDER BY mois;
```

| mois | ca_ht |
|---|---|
| 2026-08 | 7256.40 |
| 2026-09 | 13914.80 |
| 2026-10 | 4338.90 |
| 2026-11 | 7174.00 |

Tests des modèles Python (SQLAlchemy) :

```bash
docker compose exec api pytest
```
