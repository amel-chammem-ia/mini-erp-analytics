-- Chiffre d'affaires HT par mois (ventes validées uniquement)
USE MiniERP;

SELECT
    FORMAT(date_vente, 'yyyy-MM') AS mois,
    COUNT(*)                      AS nb_ventes,
    SUM(total_ht)                 AS ca_ht
FROM dbo.ventes
WHERE statut = N'validee'
GROUP BY FORMAT(date_vente, 'yyyy-MM')
ORDER BY mois;
