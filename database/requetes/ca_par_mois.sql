-- Chiffre d'affaires HT par mois (ventes validées uniquement)
-- Les dates sont enregistrées en UTC (SYSUTCDATETIME). On les convertit en heure de Paris
-- AVANT de prendre le mois : une vente du 1er décembre à 0 h 30 (Paris), enregistrée le
-- 30 novembre à 23 h 30 UTC, appartient à décembre. (Bug corrigé à l'épisode 9.)
-- 'Romance Standard Time' est le nom SQL Server du fuseau de Paris (heure d'été comprise).
USE MiniERP;

WITH ventes_paris AS (
    SELECT
        FORMAT(date_vente AT TIME ZONE 'UTC' AT TIME ZONE 'Romance Standard Time', 'yyyy-MM') AS mois,
        total_ht
    FROM dbo.ventes
    WHERE statut = N'validee'
)
SELECT
    mois,
    COUNT(*)      AS nb_ventes,
    SUM(total_ht) AS ca_ht
FROM ventes_paris
GROUP BY mois
ORDER BY mois;
