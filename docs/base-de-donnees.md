# Base de données · Mini-ERP Analytics

Créée à l'épisode 7. La base `MiniERP` (SQL Server 2022) compte cinq tables.

```text
clients 1 ───< ventes 1 ───< lignes_vente >─── 1 produits
                  │                                  │
                  └──────< mouvements_stock >─────── 1
```

| Table | Rôle | Règles principales |
|---|---|---|
| `clients` | Les entreprises clientes | e-mail et n° de TVA uniques, format d'e-mail contrôlé |
| `produits` | Le catalogue | référence unique, prix et stock positifs, TVA entre 0 et 100 |
| `ventes` | Les commandes | numéro unique, statut `brouillon`, `validee` ou `annulee` |
| `lignes_vente` | Le détail de chaque vente | quantité > 0, un produit une seule fois par vente, suppression en cascade avec la vente |
| `mouvements_stock` | L'historique des entrées et sorties | type `entree` ou `sortie`, quantité > 0 |

## Choix de conception

| Choix | Pourquoi |
|---|---|
| Montants en `DECIMAL(12,2)` et `DECIMAL(14,2)` | `FLOAT` stocke une valeur approchée : les centimes s'arrondissent mal. |
| Prix et TVA recopiés dans chaque ligne de vente | Une facture ne doit pas changer si le prix du produit change ensuite. |
| Contraintes `CHECK`, `UNIQUE` et clés étrangères dans la base | Les règles métier restent vraies même si une autre application écrit dans la base. |
| Index sur `ventes.date_vente`, `ventes.client_id`, `lignes_vente.produit_id`, `mouvements_stock (produit_id, date_mouvement)` | Ce sont les colonnes filtrées et jointes par les analyses. |
| Dates en `DATETIME2(0)` UTC | Précision à la seconde, pas d'ambiguïté de fuseau. |
| Scripts relançables (`IF ... IS NULL`, `IF NOT EXISTS`) | `docker compose up` peut être relancé sans erreur. |

## Fichiers

| Fichier | Contenu |
|---|---|
| `database/01_schema.sql` | Création de la base, des tables, des contraintes et des index |
| `database/02_seed.sql` | Données de test fictives : 8 clients, 10 produits, 14 ventes sur 4 mois |
| `database/init.sh` | Exécute les deux scripts (service `db-init` de Docker Compose) |
| `database/requetes/ca_par_mois.sql` | Chiffre d'affaires HT par mois |
| `backend/app/models.py` | Les mêmes tables, vues depuis Python (SQLAlchemy) |

## Les données de test

Les entreprises, e-mails (domaines `.example`) et numéros de TVA sont fictifs. Le stock de chaque produit est cohérent avec ses mouvements : une entrée de stock initial, puis une sortie par ligne de vente validée. Deux produits sont volontairement sous leur seuil d'alerte (écran 24", casque), pour l'épisode 12.

Résultat de `ca_par_mois.sql` :

| mois | ca_ht (€) |
|---|---|
| 2026-08 | 7 256,40 |
| 2026-09 | 13 914,80 |
| 2026-10 | 4 338,90 |
| 2026-11 | 7 174,00 |

## Se connecter à la base

Depuis SQL Server Management Studio, Azure Data Studio ou VS Code : serveur `localhost,1433`, utilisateur `sa`, mot de passe de votre fichier `.env`, et cochez « Trust server certificate ».
