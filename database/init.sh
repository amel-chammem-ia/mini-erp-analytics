#!/bin/bash
# Crée la base MiniERP, charge les données de test (épisode 7) et numérote les factures (épisode 11).
# Exécuté par le service db-init de docker-compose, une fois SQL Server prêt.
set -euo pipefail

SQLCMD=/opt/mssql-tools18/bin/sqlcmd

for script in /database/01_schema.sql /database/02_seed.sql /database/03_factures.sql; do
  echo "Exécution de ${script}..."
  "${SQLCMD}" -S db -U sa -P "${MSSQL_SA_PASSWORD}" -C -b -I -i "${script}"
done

echo "Base MiniERP prête."
