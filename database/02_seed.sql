-- Mini-ERP Analytics · données de test (épisode 7)
-- Entreprises et adresses entièrement fictives (domaines .example).
-- Relançable sans erreur : rien n'est inséré si des clients existent déjà.
USE MiniERP;
GO
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;  -- la table ventes a un index filtré (épisode 11)

IF NOT EXISTS (SELECT 1 FROM dbo.clients)
BEGIN
    BEGIN TRANSACTION;

    SET IDENTITY_INSERT dbo.clients ON;
    INSERT INTO dbo.clients (id, nom, email, numero_tva, ville) VALUES
        (1, N'Atelier Numérique', N'contact@atelier-numerique.example', N'FR01000000001', N'Lyon'),
        (2, N'Cabinet Martin & Associés', N'compta@cabinet-martin.example', N'FR02000000002', N'Paris'),
        (3, N'Boulangerie des Halles', N'gerance@boulangerie-halles.example', N'FR03000000003', N'Nantes'),
        (4, N'Studio Pixel Ouest', N'hello@studio-pixel.example', N'FR04000000004', N'Rennes'),
        (5, N'Clinique Vétérinaire du Parc', N'accueil@clinique-parc.example', N'FR05000000005', N'Bordeaux'),
        (6, N'Transports Lefèvre', N'achats@transports-lefevre.example', N'FR06000000006', N'Lille'),
        (7, N'École Horizon', N'direction@ecole-horizon.example', N'FR07000000007', N'Toulouse'),
        (8, N'Agence Immobilière Azur', N'agence@immo-azur.example', N'FR08000000008', N'Nice');
    SET IDENTITY_INSERT dbo.clients OFF;

    SET IDENTITY_INSERT dbo.produits ON;
    INSERT INTO dbo.produits (id, reference, nom, categorie, prix_ht, taux_tva, stock_actuel, seuil_alerte) VALUES
        (1, N'P-001', N'Ordinateur portable 14" Pro', N'Ordinateurs', 899.00, 20.00, 18, 5),
        (2, N'P-002', N'Ordinateur de bureau compact', N'Ordinateurs', 649.00, 20.00, 9, 3),
        (3, N'P-003', N'Écran 27" QHD', N'Écrans', 279.00, 20.00, 22, 5),
        (4, N'P-004', N'Écran 24" Full HD', N'Écrans', 159.00, 20.00, 4, 5),
        (5, N'P-005', N'Clavier sans fil', N'Accessoires', 49.90, 20.00, 35, 10),
        (6, N'P-006', N'Souris ergonomique', N'Accessoires', 39.90, 20.00, 41, 10),
        (7, N'P-007', N'Station d''accueil USB-C', N'Accessoires', 189.00, 20.00, 7, 4),
        (8, N'P-008', N'Casque à réduction de bruit', N'Audio', 129.00, 20.00, 2, 5),
        (9, N'P-009', N'Imprimante laser couleur', N'Impression', 349.00, 20.00, 6, 2),
        (10, N'P-010', N'Disque SSD externe 1 To', N'Stockage', 99.90, 20.00, 15, 8);
    SET IDENTITY_INSERT dbo.produits OFF;

    SET IDENTITY_INSERT dbo.ventes ON;
    INSERT INTO dbo.ventes (id, numero, client_id, date_vente, statut, total_ht, total_tva, total_ttc) VALUES
        (1, N'V-2026-0001', 1, '2026-08-04 10:15', N'validee', 3683.70, 736.74, 4420.44),
        (2, N'V-2026-0002', 3, '2026-08-12 14:40', N'validee', 847.90, 169.58, 1017.48),
        (3, N'V-2026-0003', 5, '2026-08-21 09:05', N'validee', 548.80, 109.76, 658.56),
        (4, N'V-2026-0004', 2, '2026-08-28 16:20', N'validee', 2176.00, 435.20, 2611.20),
        (5, N'V-2026-0005', 4, '2026-09-03 11:00', N'validee', 5228.00, 1045.60, 6273.60),
        (6, N'V-2026-0006', 6, '2026-09-15 15:30', N'validee', 2693.40, 538.68, 3232.08),
        (7, N'V-2026-0007', 7, '2026-09-24 10:45', N'validee', 5993.40, 1198.68, 7192.08),
        (8, N'V-2026-0008', 8, '2026-10-02 09:30', N'validee', 1285.00, 257.00, 1542.00),
        (9, N'V-2026-0009', 1, '2026-10-09 13:10', N'validee', 898.00, 179.60, 1077.60),
        (10, N'V-2026-0010', 2, '2026-10-17 17:05', N'annulee', 899.00, 179.80, 1078.80),
        (11, N'V-2026-0011', 5, '2026-10-23 10:00', N'validee', 2155.90, 431.18, 2587.08),
        (12, N'V-2026-0012', 4, '2026-11-05 14:15', N'validee', 1962.00, 392.40, 2354.40),
        (13, N'V-2026-0013', 6, '2026-11-13 09:50', N'validee', 5212.00, 1042.40, 6254.40),
        (14, N'V-2026-0014', 3, '2026-11-20 16:35', N'brouillon', 179.60, 35.92, 215.52);
    SET IDENTITY_INSERT dbo.ventes OFF;

    SET IDENTITY_INSERT dbo.lignes_vente ON;
    INSERT INTO dbo.lignes_vente (id, vente_id, produit_id, quantite, prix_unitaire_ht, taux_tva) VALUES
        (1, 1, 1, 3, 899.00, 20.00),
        (2, 1, 3, 3, 279.00, 20.00),
        (3, 1, 5, 3, 49.90, 20.00),
        (4, 2, 2, 1, 649.00, 20.00),
        (5, 2, 4, 1, 159.00, 20.00),
        (6, 2, 6, 1, 39.90, 20.00),
        (7, 3, 9, 1, 349.00, 20.00),
        (8, 3, 10, 2, 99.90, 20.00),
        (9, 4, 1, 2, 899.00, 20.00),
        (10, 4, 7, 2, 189.00, 20.00),
        (11, 5, 1, 4, 899.00, 20.00),
        (12, 5, 3, 4, 279.00, 20.00),
        (13, 5, 8, 4, 129.00, 20.00),
        (14, 6, 2, 3, 649.00, 20.00),
        (15, 6, 4, 3, 159.00, 20.00),
        (16, 6, 5, 3, 49.90, 20.00),
        (17, 6, 6, 3, 39.90, 20.00),
        (18, 7, 1, 6, 899.00, 20.00),
        (19, 7, 10, 6, 99.90, 20.00),
        (20, 8, 9, 1, 349.00, 20.00),
        (21, 8, 7, 2, 189.00, 20.00),
        (22, 8, 3, 2, 279.00, 20.00),
        (23, 9, 5, 10, 49.90, 20.00),
        (24, 9, 6, 10, 39.90, 20.00),
        (25, 10, 1, 1, 899.00, 20.00),
        (26, 11, 1, 2, 899.00, 20.00),
        (27, 11, 8, 2, 129.00, 20.00),
        (28, 11, 10, 1, 99.90, 20.00),
        (29, 12, 3, 5, 279.00, 20.00),
        (30, 12, 7, 3, 189.00, 20.00),
        (31, 13, 1, 4, 899.00, 20.00),
        (32, 13, 2, 2, 649.00, 20.00),
        (33, 13, 4, 2, 159.00, 20.00),
        (34, 14, 5, 2, 49.90, 20.00),
        (35, 14, 6, 2, 39.90, 20.00);
    SET IDENTITY_INSERT dbo.lignes_vente OFF;

    -- Stock initial (entrées) puis une sortie par ligne de vente validée :
    -- le stock actuel de chaque produit est égal à la somme de ses mouvements.
    INSERT INTO dbo.mouvements_stock (produit_id, type_mouvement, quantite, date_mouvement, vente_id, commentaire) VALUES
        (1, N'entree', 39, '2026-08-01 08:00', NULL, N'Stock initial'),
        (2, N'entree', 15, '2026-08-01 08:00', NULL, N'Stock initial'),
        (3, N'entree', 36, '2026-08-01 08:00', NULL, N'Stock initial'),
        (4, N'entree', 10, '2026-08-01 08:00', NULL, N'Stock initial'),
        (5, N'entree', 51, '2026-08-01 08:00', NULL, N'Stock initial'),
        (6, N'entree', 55, '2026-08-01 08:00', NULL, N'Stock initial'),
        (7, N'entree', 14, '2026-08-01 08:00', NULL, N'Stock initial'),
        (8, N'entree', 8, '2026-08-01 08:00', NULL, N'Stock initial'),
        (9, N'entree', 8, '2026-08-01 08:00', NULL, N'Stock initial'),
        (10, N'entree', 24, '2026-08-01 08:00', NULL, N'Stock initial'),
        (1, N'sortie', 3, '2026-08-04 10:15', 1, N'Vente V-2026-0001'),
        (3, N'sortie', 3, '2026-08-04 10:15', 1, N'Vente V-2026-0001'),
        (5, N'sortie', 3, '2026-08-04 10:15', 1, N'Vente V-2026-0001'),
        (2, N'sortie', 1, '2026-08-12 14:40', 2, N'Vente V-2026-0002'),
        (4, N'sortie', 1, '2026-08-12 14:40', 2, N'Vente V-2026-0002'),
        (6, N'sortie', 1, '2026-08-12 14:40', 2, N'Vente V-2026-0002'),
        (9, N'sortie', 1, '2026-08-21 09:05', 3, N'Vente V-2026-0003'),
        (10, N'sortie', 2, '2026-08-21 09:05', 3, N'Vente V-2026-0003'),
        (1, N'sortie', 2, '2026-08-28 16:20', 4, N'Vente V-2026-0004'),
        (7, N'sortie', 2, '2026-08-28 16:20', 4, N'Vente V-2026-0004'),
        (1, N'sortie', 4, '2026-09-03 11:00', 5, N'Vente V-2026-0005'),
        (3, N'sortie', 4, '2026-09-03 11:00', 5, N'Vente V-2026-0005'),
        (8, N'sortie', 4, '2026-09-03 11:00', 5, N'Vente V-2026-0005'),
        (2, N'sortie', 3, '2026-09-15 15:30', 6, N'Vente V-2026-0006'),
        (4, N'sortie', 3, '2026-09-15 15:30', 6, N'Vente V-2026-0006'),
        (5, N'sortie', 3, '2026-09-15 15:30', 6, N'Vente V-2026-0006'),
        (6, N'sortie', 3, '2026-09-15 15:30', 6, N'Vente V-2026-0006'),
        (1, N'sortie', 6, '2026-09-24 10:45', 7, N'Vente V-2026-0007'),
        (10, N'sortie', 6, '2026-09-24 10:45', 7, N'Vente V-2026-0007'),
        (9, N'sortie', 1, '2026-10-02 09:30', 8, N'Vente V-2026-0008'),
        (7, N'sortie', 2, '2026-10-02 09:30', 8, N'Vente V-2026-0008'),
        (3, N'sortie', 2, '2026-10-02 09:30', 8, N'Vente V-2026-0008'),
        (5, N'sortie', 10, '2026-10-09 13:10', 9, N'Vente V-2026-0009'),
        (6, N'sortie', 10, '2026-10-09 13:10', 9, N'Vente V-2026-0009'),
        (1, N'sortie', 2, '2026-10-23 10:00', 11, N'Vente V-2026-0011'),
        (8, N'sortie', 2, '2026-10-23 10:00', 11, N'Vente V-2026-0011'),
        (10, N'sortie', 1, '2026-10-23 10:00', 11, N'Vente V-2026-0011'),
        (3, N'sortie', 5, '2026-11-05 14:15', 12, N'Vente V-2026-0012'),
        (7, N'sortie', 3, '2026-11-05 14:15', 12, N'Vente V-2026-0012'),
        (1, N'sortie', 4, '2026-11-13 09:50', 13, N'Vente V-2026-0013'),
        (2, N'sortie', 2, '2026-11-13 09:50', 13, N'Vente V-2026-0013'),
        (4, N'sortie', 2, '2026-11-13 09:50', 13, N'Vente V-2026-0013');

    COMMIT TRANSACTION;
END
GO
