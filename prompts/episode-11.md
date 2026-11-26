# Épisode 11 · Ventes et factures

Objectif : enregistrer une commande, calculer ses totaux au centime près, la valider et produire une facture PDF. Le piège : l'argent. Un `float` et une règle d'arrondi floue, et la facture n'est plus juste.

## 1. D'abord les règles de calcul (sans IA)

On écrit les règles avant le prompt. Le détail est dans [`docs/factures.md`](../docs/factures.md) :

- jamais de `float` : des `Decimal` partout ;
- montant HT d'une ligne = quantité × prix unitaire, arrondi au centime ;
- TVA calculée par taux, sur le total HT de ce taux ;
- arrondi commercial (0,005 € et plus → centime supérieur) ;
- TTC = HT + TVA.

Le test qui fixe la règle : trois lignes à 0,99 € HT, TVA 20 % → 0,59 € de TVA (par taux), et non 0,60 € (ligne par ligne).

## 2. Le prompt de génération

```text
Rôle : tu es un développeur Python senior, spécialiste des logiciels de facturation.
Contexte : API FastAPI + SQLAlchemy + SQL Server (fichiers joints). Une vente a des lignes (produit, quantité, prix unitaire HT, taux de TVA). Statuts : brouillon, validée, annulée.
Tâche : écris le calcul des totaux, les routes des ventes et la facture PDF.
Règles de calcul (à respecter à la lettre) :
- montants en Decimal uniquement, jamais de float ; refuse un float avec une erreur ;
- montant HT d'une ligne = quantité × prix unitaire HT, arrondi au centime (ROUND_HALF_UP) ;
- TVA calculée par taux, sur le total HT de ce taux, puis arrondie au centime ;
- TTC = total HT + total TVA.
Règles métier :
- le prix et le taux de TVA viennent du catalogue, jamais de la requête ;
- la validation se fait en une seule transaction : sortie du stock (refusée si le stock manque), numéro de facture, statut validé ;
- numéro de facture FAC-AAAA-NNNNN, unique, chronologique, sans trou : un échec de validation ne consomme pas de numéro ;
- une vente validée n'est plus modifiable ;
- la facture PDF porte les mentions obligatoires entre professionnels en France.
Format : d'abord le module de calcul seul (sans FastAPI ni base) et ses tests pytest, ensuite les routes, ensuite le PDF.

[coller ici models.py, schemas.py, droits.py et un routeur existant]
```

## 3. Le prompt de vérification

```text
Rôle : tu es contrôleur de gestion. Tu vérifies des factures, pas du code.
Voici 5 commandes (lignes, prix, taux) et les totaux calculés par l'application.
Recalcule chaque total à la main, en suivant exactement les règles ci-dessous, et signale le moindre centime d'écart.
Ajoute 5 cas pièges de ton choix (0,99 €, taux à 5,5 %, montant en ,005, grosse quantité, plusieurs taux) avec le résultat attendu.
Format : un tableau commande / attendu / obtenu / écart, puis les cas pièges au format pytest.
```

## 4. La relecture : trois questions

- [ ] **Un `float` traîne-t-il quelque part ?** Recherchez `float(` et les littéraux comme `0.2` dans le code des montants.
- [ ] **Les totaux tombent-ils juste ?** HT + TVA = TTC, au centime, sur tous les tests.
- [ ] **Une facture peut-elle changer après coup ?** Prix copié à la commande, vente validée figée, numéro jamais réutilisé.

## 5. Tester

```bash
docker compose up --build                     # ajoute les colonnes de facturation et numérote les ventes existantes
docker compose exec api pytest tests/test_montants.py tests/test_facture_pdf.py   # sans base, en une seconde
docker compose exec api pytest                # toute l'API
```
