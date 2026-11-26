-- Mini-ERP Analytics · numérotation des factures déjà validées (épisode 11)
-- Les ventes validées des données de test n'ont pas encore de numéro de facture.
-- On les numérote une fois, dans l'ordre chronologique (heure de Paris), puis on règle
-- le compteur de chaque année sur le dernier numéro attribué.
-- Relançable sans erreur : ne fait rien si une facture est déjà numérotée.
USE MiniERP;
GO
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;  -- index filtré sur ventes.numero_facture
GO

IF NOT EXISTS (SELECT 1 FROM dbo.ventes WHERE numero_facture IS NOT NULL)
   AND NOT EXISTS (SELECT 1 FROM dbo.compteurs_factures)
BEGIN
    BEGIN TRANSACTION;

    WITH a_numeroter AS (
        SELECT numero_facture, facturee_le, date_vente,
               YEAR(date_vente AT TIME ZONE 'UTC' AT TIME ZONE 'Romance Standard Time') AS annee,
               ROW_NUMBER() OVER (
                   PARTITION BY YEAR(date_vente AT TIME ZONE 'UTC' AT TIME ZONE 'Romance Standard Time')
                   ORDER BY date_vente, id) AS rang
        FROM dbo.ventes
        WHERE statut = N'validee'
    )
    UPDATE a_numeroter
    SET numero_facture = CONCAT(N'FAC-', annee, N'-', RIGHT(CONCAT(N'0000', rang), 5)),
        facturee_le = date_vente;

    INSERT INTO dbo.compteurs_factures (annee, dernier_numero)
    SELECT CAST(SUBSTRING(numero_facture, 5, 4) AS INT), MAX(CAST(RIGHT(numero_facture, 5) AS INT))
    FROM dbo.ventes
    WHERE numero_facture IS NOT NULL
    GROUP BY SUBSTRING(numero_facture, 5, 4);

    COMMIT TRANSACTION;
END
GO
