# L'API · clients et produits

Mise en place à l'épisode 8, protégée par connexion et rôles depuis l'épisode 10 (voir [`droits.md`](droits.md)). Documentation interactive (générée par FastAPI) : http://localhost:8000/docs

## Les routes

Toutes les routes, sauf `/api/health` et `/api/auth/connexion`, exigent l'en-tête `Authorization: Bearer <jeton>`. La colonne « Droit » renvoie à la matrice de [`droits.md`](droits.md).

| Méthode | Route | Rôle | Droit | Réponse |
|---|---|---|---|---|
| `POST` | `/api/auth/connexion` | Se connecter : e-mail et mot de passe contre un jeton de 30 minutes (épisode 10) | aucun | 200 · 401 · 429 |
| `GET` | `/api/auth/moi` | Mon compte et la liste de mes droits | connecté | 200 · 401 |
| `GET` | `/api/utilisateurs` | Lister les comptes | `utilisateurs:gerer` | 200 |
| `POST` | `/api/utilisateurs` | Créer un compte | `utilisateurs:gerer` | 201 · 409 · 422 |
| `PATCH` | `/api/utilisateurs/{id}` | Changer le nom, le rôle, le mot de passe, activer ou désactiver | `utilisateurs:gerer` | 200 · 404 · 409 · 422 |
| `GET` | `/api/clients?recherche=&page=1&taille=20` | Rechercher des clients (nom, e-mail ou ville) | `clients:lire` | 200, une page |
| `GET` | `/api/clients/{id}` | Lire un client | `clients:lire` | 200 · 404 |
| `POST` | `/api/clients` | Créer un client | `clients:ecrire` | 201 · 409 · 422 |
| `PATCH` | `/api/clients/{id}` | Modifier un client (seulement les champs envoyés) | `clients:ecrire` | 200 · 404 · 409 · 422 |
| `DELETE` | `/api/clients/{id}` | Supprimer un client sans vente | `clients:supprimer` | 204 · 404 · 409 |
| `GET` | `/api/produits?recherche=&categorie=&sous_le_seuil=&inclure_archives=false` | Rechercher des produits | `produits:lire` | 200, une page |
| `GET` | `/api/produits/{id}` | Lire un produit | `produits:lire` | 200 · 404 |
| `POST` | `/api/produits` | Créer un produit (stock à 0) | `produits:ecrire` | 201 · 409 · 422 |
| `PATCH` | `/api/produits/{id}` | Modifier un produit (la référence ne change pas) | `produits:ecrire` | 200 · 404 · 422 |
| `DELETE` | `/api/produits/{id}` | Archiver un produit | `produits:ecrire` | 204 · 404 |
| `GET` | `/api/statistiques/ca-par-mois` | Chiffre d'affaires HT par mois, ventes validées, en heure de Paris (épisode 9) | `statistiques:lire` | 200 |

Une page de résultats a toujours la même forme :

```json
{ "items": [ ... ], "total": 13, "page": 1, "taille": 20 }
```

`taille` vaut 20 par défaut (cahier des charges, US-02) et 100 au maximum.

## Les codes d'erreur

| Code | Quand | Exemple |
|---|---|---|
| `401` | Pas connecté : jeton absent, expiré ou falsifié, compte désactivé (épisode 10) | `GET /api/clients` sans en-tête `Authorization` |
| `403` | Connecté, mais le rôle ne permet pas l'action (épisode 10) | un vendeur qui crée un produit |
| `404` | La ressource n'existe pas | `GET /api/clients/999` |
| `409` | Conflit avec une donnée existante | e-mail ou numéro de TVA déjà utilisé, référence produit en double, suppression d'un client qui a des ventes |
| `422` | Donnée invalide, refusée avant d'atteindre la base | e-mail mal formé, prix négatif ou à 3 décimales, TVA hors de 0 à 100, champ inconnu, `null` sur un champ obligatoire |
| `429` | Trop d'échecs de connexion : 5 en 15 minutes sur un e-mail (épisode 10) | `POST /api/auth/connexion` |

## Les règles métier

- Les entrées sont **normalisées** : espaces retirés, e-mail en minuscules, numéro de TVA et référence en majuscules.
- Un champ inconnu est **refusé** (`extra="forbid"`) : impossible d'envoyer `"stock_actuel": 50` ou `"role": "admin"`.
- Le **stock** ne se saisit pas : un produit est créé à 0 et son stock ne bouge que par des mouvements de stock (épisode 12).
- Un **client** qui a des ventes ne se supprime pas : ses factures doivent rester lisibles.
- Un **produit** ne disparaît jamais : `DELETE` l'archive (`actif = false`). Il n'apparaît plus dans les listes, sauf avec `inclure_archives=true`, et `PATCH {"actif": true}` le réactive.
- La recherche traite `%`, `_` et `[` comme des caractères ordinaires : chercher « 100% » ne renvoie pas tout.
- Les **dates** sont enregistrées en UTC et renvoyées avec leur fuseau (`"2026-11-30T23:30:00Z"`). Les regroupements par mois se font en heure de Paris (épisode 9, voir [`debogage.md`](debogage.md)).

## Exemple

Se connecter, puis garder le jeton dans une variable :

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/connexion \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@votre-entreprise.fr", "mot_de_passe": "votre-mot-de-passe"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

Dans la documentation interactive (`/docs`), le bouton **Authorize** accepte ce jeton.

```bash
curl -X POST http://localhost:8000/api/clients \
  -H "Authorization: Bearer $TOKEN" \
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
| `backend/app/securite.py` | Hachage des mots de passe, jetons signés, limite de tentatives (épisode 10) |
| `backend/app/droits.py` | Matrice des droits par rôle (épisode 10) |
| `backend/app/acces.py` | Dépendances `utilisateur_courant` et `autoriser(...)` (épisode 10) |
| `backend/app/routers/auth.py`, `utilisateurs.py` | Routes `/api/auth` et `/api/utilisateurs` (épisode 10) |
| `backend/app/creer_admin.py` | Création du premier administrateur en ligne de commande (épisode 10) |
| `backend/tests/test_api_clients.py`, `test_api_produits.py`, `test_api_auth.py` | Tests de l'API, sur une base SQLite en mémoire |
| `backend/tests/test_securite.py`, `test_droits.py` | Tests sans serveur ni base (épisode 10) |
