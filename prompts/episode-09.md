# Épisode 9 · Tests et débogage

Objectif : faire écrire par l'IA des tests qui trouvent les vrais bugs, puis corriger un bug réel avec une méthode : reproduire, comprendre, corriger, garder le test.

## 1. Le prompt pour écrire des tests

```text
Rôle : tu es un ingénieur qualité, expert pytest.
Contexte : voici la fonction à tester (ci-dessous) et la règle métier : le chiffre d'affaires d'un mois regroupe les ventes validées de ce mois, en heure de Paris. Les dates sont enregistrées en UTC.
Tâche : écris les tests pytest de cette fonction.
Contraintes :
- trois familles de cas : le cas normal, les limites, les erreurs ;
- pour les limites, pense au temps : minuit le 1er du mois, le dernier jour du mois, l'heure d'été et l'heure d'hiver ;
- un test = une règle, avec un nom qui la décrit en français ;
- aucune base de données réelle : des données en mémoire.
Format : le fichier de tests complet, puis la liste des cas couverts et de ceux qui ne le sont pas.

[coller ici la fonction]
```

## 2. Le prompt de débogage

```text
Rôle : tu es un expert en débogage Python et SQL Server.
Symptôme : une vente du 1er décembre à 0 h 30 apparaît dans le chiffre d'affaires de novembre.
Attendu : "2026-12". Obtenu : "2026-11".
Reproduction : le test test_vente_du_1er_decembre_a_0h30_comptee_en_decembre échoue (sortie ci-dessous).
Contexte : les dates sont enregistrées avec SYSUTCDATETIME(). Voici la fonction, la requête SQL et la sortie de pytest.
Tâche : ne corrige rien pour l'instant. Donne trois hypothèses classées de la plus probable à la moins probable, et pour chacune la vérification qui la confirme ou l'écarte.
Ensuite seulement : propose la plus petite correction, et dis où le même bug peut se cacher ailleurs dans le code.

[coller ici la fonction, la requête SQL et la sortie de pytest]
```

## 3. La relecture : trois questions

- [ ] **Le test échouait-il avant la correction ?** Un test qui passe déjà ne prouve rien : il doit être rouge avant, vert après.
- [ ] **La cause est-elle expliquée, pas seulement le symptôme ?** Ici : dates en UTC, regroupement sans conversion en heure de Paris.
- [ ] **Le même bug existe-t-il ailleurs ?** Ici : la requête SQL de l'épisode 7, et les dates renvoyées par l'API sans fuseau.

## 4. Lancer les tests

```bash
docker compose exec api pytest
docker compose exec api pytest -k decembre
```

La méthode complète et la fiche du bug sont dans [`docs/debogage.md`](../docs/debogage.md).
