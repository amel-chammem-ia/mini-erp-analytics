# Ventes et factures

Mises en place à l'épisode 11 (cahier des charges : US-04 et US-05).

## Le cycle de vie d'une vente

```text
brouillon ──valider──▶ validée   (stock sorti, numéro de facture attribué, plus modifiable)
    └────annuler──▶ annulée
```

| Action | Qui (voir [`droits.md`](droits.md)) | Ce qui se passe |
|---|---|---|
| Créer une commande | vendeur, administrateur | Brouillon. Prix et TVA copiés depuis le catalogue, totaux calculés |
| Modifier | vendeur, administrateur | Seulement un brouillon |
| Valider | vendeur, administrateur | En une seule transaction : sortie du stock, numéro de facture, vente figée |
| Annuler | vendeur, administrateur | Seulement un brouillon. Une facture validée ne s'annule pas : il faut une facture d'avoir (non couvert) |
| Télécharger la facture PDF | tous ceux qui lisent les ventes | Seulement une vente validée |

## Les règles de calcul

Décidées **avant** d'écrire le prompt, puis vérifiées par [`test_montants.py`](../backend/tests/test_montants.py).

1. **Jamais de `float` pour de l'argent.** En `float`, `0.1 + 0.2` vaut `0.30000000000000004`, et `round(2.675, 2)` donne `2.67`. Tous les montants sont des `Decimal`, côté Python comme côté SQL Server (`DECIMAL(12, 2)`). Le module refuse un `float`.
2. **Montant HT d'une ligne** = quantité × prix unitaire HT, arrondi au centime.
3. **La TVA se calcule par taux, sur le total HT de ce taux**, puis s'arrondit au centime.
4. **Arrondi commercial** : à partir de 0,005 €, on arrondit au centime supérieur (`ROUND_HALF_UP`).
5. **TTC = total HT + total TVA.** Les trois totaux restent cohérents, au centime près.

### Le centime qui change tout

Trois lignes à 0,99 € HT, TVA 20 % :

| Méthode | Calcul | TVA |
|---|---|---|
| Ligne par ligne, puis somme | 0,198 → 0,20, trois fois | **0,60 €** |
| Par taux, sur le total HT (retenue) | 2,97 × 20 % = 0,594 → 0,59 | **0,59 €** |

Les deux méthodes se défendent, mais une application doit en choisir **une** et s'y tenir. Sinon, la facture, l'export comptable et le tableau de bord ne tombent pas juste. Le choix est écrit ici, dans le prompt et dans un test.

## La numérotation des factures

- Format : `FAC-2026-00001`, un compteur par année (en heure de Paris).
- **Unique, chronologique, sans trou** : le compteur (`compteurs_factures`) est verrouillé et incrémenté dans la même transaction que la validation. Si la validation échoue (stock insuffisant, par exemple), le numéro n'est pas consommé.
- Le numéro de commande (`V-2026-0042`) est différent : il existe dès le brouillon.
- Unicité garantie aussi par la base : index unique filtré `ux_ventes_numero_facture` (les brouillons n'ont pas de numéro).

## Le stock à la validation

Chaque sortie est un `UPDATE … WHERE stock_actuel >= quantité` : deux vendeurs qui valident en même temps ne peuvent pas vendre la même dernière unité. Si une seule ligne manque de stock, rien n'est enregistré et l'API répond `409` avec le détail :

```json
{"detail": "Stock insuffisant : P-008 (demandé 5, disponible 2)"}
```

Chaque sortie crée un mouvement de stock lié à la vente (historique, US-08).

## La facture PDF

Générée avec ReportLab par [`facture_pdf.py`](../backend/app/facture_pdf.py). Mentions présentes (factures entre professionnels, France) : numéro, date d'émission, identité et n° de TVA du vendeur et du client, désignation, quantité, prix unitaire HT, taux de TVA, totaux HT, TVA par taux et TTC, échéance (30 jours), pénalités de retard, indemnité forfaitaire de 40 € et absence d'escompte.

L'émetteur se règle dans le fichier `.env` (variables facultatives) :

```text
ENTREPRISE_NOM=Votre entreprise SAS
ENTREPRISE_ADRESSE=12 rue de l'Exemple|69002 Lyon
ENTREPRISE_TVA=FR00123456789
ENTREPRISE_SIRET=123 456 789 00012
```

Vérifiez les mentions obligatoires avec votre expert-comptable avant d'émettre de vraies factures.

## Mise à jour d'une base existante

`docker compose up --build` relance `db-init`, qui ajoute les colonnes de facturation et le compteur (`01_schema.sql`), puis numérote une fois les ventes déjà validées des données de test (`03_factures.sql`).

## Limites connues

- Pas de facture d'avoir : une vente validée ne s'annule pas encore.
- Pas de remise ni de frais de port.
- La facture n'est pas archivée en PDF : elle est régénérée à la demande, à l'identique, à partir des données figées de la vente.
