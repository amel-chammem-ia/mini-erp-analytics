# Cahier des charges · Mini-ERP Analytics

Version 1.0 · rédigé avec l'IA (épisode 5), relu, corrigé et validé par la cheffe de projet.

## 1. Contexte

Une PME de 20 personnes vend du matériel informatique (ordinateurs, écrans, accessoires) à des entreprises et à des particuliers. Aujourd'hui, les clients, les commandes et le stock sont suivis dans plusieurs fichiers Excel :

- les doublons de clients sont fréquents ;
- le stock n'est pas à jour, des ventes sont validées sur des produits en rupture ;
- le dirigeant attend plusieurs jours pour connaître le chiffre d'affaires du mois.

## 2. Objectif

Remplacer les fichiers Excel par une application web unique qui centralise les clients, les produits, les ventes et le stock, et qui fournit des tableaux de bord à jour, partageables avec l'équipe.

## 3. Utilisateurs et rôles

| Rôle | Description | Droits principaux |
|---|---|---|
| Commercial | Prospecte et suit les clients | Clients : lecture, création, modification |
| Vendeur | Enregistre les commandes | Ventes : création, validation ; produits : lecture |
| Magasinier | Gère les entrées et sorties de stock | Stock : mouvements, seuils |
| Manager | Pilote l'activité de l'équipe | Tableaux de bord : lecture, partage |
| Dirigeant | Suit les résultats de l'entreprise | Lecture de tout, tableaux de bord |
| Administrateur | Gère les comptes | Utilisateurs et rôles |

## 4. User stories

| ID | En tant que | je veux | afin de | Critères d'acceptation |
|---|---|---|---|---|
| US-01 | Commercial | créer une fiche client | centraliser les informations | Nom, e-mail et n° de TVA obligatoires ; e-mail au bon format ; refus d'un doublon (même e-mail ou même n° de TVA) |
| US-02 | Commercial | rechercher un client | le retrouver rapidement | Recherche par nom, e-mail ou ville ; résultats paginés par 20 ; réponse en moins d'une seconde |
| US-03 | Vendeur | consulter le catalogue produits | conseiller le client | Référence, nom, catégorie, prix HT, taux de TVA et stock disponible affichés |
| US-04 | Vendeur | enregistrer une commande | facturer le client | Au moins une ligne ; quantité supérieure à 0 ; stock vérifié avant validation ; total HT, TVA et TTC calculés automatiquement |
| US-05 | Vendeur | générer la facture d'une commande validée | l'envoyer au client | Numéro de facture unique et chronologique ; export PDF ; une commande validée n'est plus modifiable |
| US-06 | Magasinier | enregistrer une entrée de stock | tenir le stock à jour | Produit, quantité et date obligatoires ; historique des mouvements conservé |
| US-07 | Magasinier | être alerté en cas de rupture | réapprovisionner à temps | Alerte quand le stock passe sous le seuil minimum du produit ; liste des produits sous le seuil |
| US-08 | Magasinier | voir les mouvements d'un produit | comprendre les écarts | Entrées et sorties datées, avec l'utilisateur et la commande liée |
| US-09 | Administrateur | gérer les comptes et les rôles | protéger les données | Connexion par e-mail et mot de passe ; mots de passe hachés ; chaque écran vérifie le rôle |
| US-10 | Dirigeant | voir le CA du mois | suivre l'activité | Graphique du CA par mois et par produit ; seules les ventes validées sont comptées |
| US-11 | Manager | filtrer les analyses | répondre à une question précise | Filtres par période, catégorie, vendeur et client ; les graphiques se mettent à jour |
| US-12 | Manager | partager un tableau de bord | informer l'équipe | Lien de partage en lecture seule, révocable ; export PDF |
| US-13 | Dirigeant | voir les meilleurs clients et produits | décider où investir | Top 10 clients et top 10 produits par CA sur la période choisie |

## 5. Exigences non fonctionnelles

- **Sécurité** : authentification obligatoire, droits par rôle, mots de passe hachés, aucun secret dans le code.
- **Qualité** : code typé, tests automatiques pour chaque règle métier, revue avant chaque intégration.
- **Performance** : pages et API en moins d'une seconde pour 10 000 ventes.
- **Déploiement** : l'application complète se lance avec Docker (interface, API, base).
- **Traçabilité** : chaque fonctionnalité est liée à son user story et au prompt qui l'a générée.

## 6. Hors périmètre (version 1)

Comptabilité générale, paie, gestion multi-entrepôts, paiement en ligne.

## 7. Validation

| Étape | Responsable | Statut |
|---|---|---|
| Génération des user stories par l'IA | Prompt n° 1 (voir `prompts/episode-05.md`) | Fait |
| Relecture et corrections (ajout du n° de TVA, doublons, factures) | Cheffe de projet | Fait |
| Validation | Cheffe de projet | Validé |
