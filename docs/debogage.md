# Tests et débogage

Mis en place à l'épisode 9.

## La méthode en 4 étapes

1. **Reproduire** : écrire un test qui échoue et qui montre le bug. Sans test qui échoue, on ne sait pas si la correction marche.
2. **Comprendre** : donner à l'IA le symptôme, le résultat attendu, le résultat obtenu et le code ; lui demander la cause **avant** la correction.
3. **Corriger** : la plus petite correction qui fait passer le test, au bon endroit (une seule fonction, réutilisée partout).
4. **Garder le test** : il devient un test de non-régression. Le bug ne peut plus revenir sans que la suite de tests le signale.

## Un bon jeu de tests couvre trois familles de cas

| Famille | Exemples dans le projet |
|---|---|
| Le cas normal | une vente au milieu du mois, un client valide |
| Les limites | minuit le 1er du mois, l'heure d'été, une page vide, 20 résultats exactement |
| Les erreurs | prix négatif (422), e-mail en double (409), client introuvable (404) |

Les bugs se cachent presque toujours dans les limites : c'est la famille à demander explicitement à l'IA.

## Fiche du bug corrigé à l'épisode 9

| | |
|---|---|
| **Symptôme** | Une vente du 1er décembre à 0 h 30 apparaît dans le chiffre d'affaires de novembre. |
| **Attendu** | `2026-12` |
| **Obtenu** | `2026-11` |
| **Cause** | Les dates sont enregistrées en UTC (`SYSUTCDATETIME()`), ce qui est la bonne pratique. Mais le calcul prenait le mois **sans convertir en heure de Paris** : 0 h 30 à Paris le 1er décembre, c'est 23 h 30 UTC le 30 novembre. L'écart est d'une heure en hiver, de deux heures en été. |
| **Présent depuis** | l'épisode 7 (`database/requetes/ca_par_mois.sql`) |
| **Correction** | `backend/app/temps.py` : `mois_metier()` convertit en heure de Paris avant de prendre le mois. La requête SQL convertit avec `AT TIME ZONE 'UTC' AT TIME ZONE 'Romance Standard Time'`. |
| **Tests ajoutés** | `backend/tests/test_temps.py` (dont `test_vente_du_1er_decembre_a_0h30_comptee_en_decembre`) et `backend/tests/test_api_statistiques.py` |
| **Même famille** | Les dates renvoyées par l'API n'indiquaient pas leur fuseau (`"2026-11-30T23:30:00"`) : un navigateur les aurait lues comme des heures locales. Elles se terminent désormais par `Z` (UTC). |

Les ventes des données de test ont toutes lieu en journée : la correction ne change pas leurs totaux (août 7 256,40 €, septembre 13 914,80 €, octobre 4 338,90 €, novembre 7 174,00 €).

## Lancer les tests

```bash
docker compose exec api pytest
```

Un seul fichier, ou un seul test :

```bash
docker compose exec api pytest tests/test_temps.py
docker compose exec api pytest -k decembre
```
