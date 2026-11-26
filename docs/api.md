# L'API · clients et produits

Mise en place à l'épisode 8. Documentation interactive (générée par FastAPI) : http://localhost:8000/docs

## Les routes

| Méthode | Route | Rôle | Réponse |
|---|---|---|---|
| `GET` | `/api/clients?recherche=&page=1&taille=20` | Rechercher des clients (nom, e-mail ou ville) | 200, une page |
| `GET` | `/api/clients/{id}` | Lire un client | 200 · 404 |
| `POST` | `/api/clients` | Créer un client | 201 · 409 · 422 |
| `PATCH` | `/api/clients/{id}` | Modifier un client (seulement les champs envoyés) | 200 · 404 · 409 · 422 |
| `DELETE` | `/api/clients/{id}` | Supprimer un client sans vente | 204 · 404 · 409 |
| `GET` | `/api/produits?recherche=&categorie=&sous_le_seuil=&inclure_archives=false` | Rechercher des produits | 200, une page |
| `GET` | `/api/produits/{id}` | Lire un produit | 200 · 404 |
| `POST` | `/api/produits` | Créer un produit (stock à 0) | 201 · 409 · 422 |
| `PATCH` | `/api/produits/{id}` | Modifier un produit (la référence ne change pas) | 200 · 404 · 422 |
| `DELETE` | `/api/produits/{id}` | Archiver un produit | 204 · 404 |
| `GET` | `/api/statistiques/ca-par-mois` | Chiffre d'affaires HT par mois, ventes validées, en heure de Paris (épisode 9) | 200 |

Une page de résultats a toujours la même forme :

```json
{ "items": [ ... ], "total": 13, "page": 1, "taille": 20 }
```

`taille` vaut 20 par défaut (cahier des charges, US-02) et 100 au maximum.

## Les codes d'erreur

| Code | Quand | Exemple |
|---|---|---|
| `404` | La ressource n'existe pas | `GET /api/clients/999` |
| `409` | Conflit avec une donnée existante | e-mail ou numéro de TVA déjà utilisé, référence produit en double, suppression d'un client qui a des ventes |
| `422` | Donnée invalide, refusée avant d'atteindre la base | e-mail mal formé, prix négatif ou à 3 décimales, TVA hors de 0 à 100, champ inconnu, `null` sur un champ obligatoire |

## Les règles métier

- Les entrées sont **normalisées** : espaces retirés, e-mail en minuscules, numéro de TVA et référence en majuscules.
- Un champ inconnu est **refusé** (`extra="forbid"`) : impossible d'envoyer `"stock_actuel": 50` ou `"role": "admin"`.
- Le **stock** ne se saisit pas : un produit est créé à 0 et son stock ne bouge que par des mouvements de stock (épisode 12).
- Un **client** qui a des ventes ne se supprime pas : ses factures doivent rester lisibles.
- Un **produit** ne disparaît jamais : `DELETE` l'archive (`actif = false`). Il n'apparaît plus dans les listes, sauf avec `inclure_archives=true`, et `PATCH {"actif": true}` le réactive.
- La recherche traite `%`, `_` et `[` comme des caractères ordinaires : chercher « 100% » ne renvoie pas tout.
- Les **dates** sont enregistrées en UTC et renvoyées avec leur fuseau (`"2026-11-30T23:30:00Z"`). Les regroupements par mois se font en heure de Paris (épisode 9, voir [`debogage.md`](debogage.md)).

## Exemple

```bash
curl -X POST http://localhost:8000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"nom": "Atelier Dupont", "email": "contact@dupont.example", "numero_tva": "FR12345678901", "ville": "Lyon"}'
```

Réponse `201` :

```json
{ "id": 9, "nom": "Atelier Dupont", "email": "contact@dupont.example", "numero_tva": "FR12345678901", "ville": "Lyon", "cree_le": "2026-11-25T15:00:00Z" }
```

Le même appel une seconde fois répond `409` : `{"detail": "Un client utilise déjà cette adresse e-mail"}`.

## Le code

| Fichier | Contenu |
|---|---|
| `backend/app/schemas.py` | Schémas Pydantic : ce que l'API accepte et renvoie |
| `backend/app/routers/clients.py` | Routes `/api/clients` |
| `backend/app/routers/produits.py` | Routes `/api/produits` |
| `backend/app/routers/commun.py` | Pagination, recherche, enregistrement |
| `backend/app/routers/statistiques.py` | Route `/api/statistiques/ca-par-mois` (épisode 9) |
| `backend/app/temps.py` | Dates UTC et mois en heure de Paris (épisode 9) |
| `backend/tests/test_api_clients.py`, `test_api_produits.py` | Tests, sur une base SQLite en mémoire |
