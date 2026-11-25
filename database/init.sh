#!/bin/bash
# Crée la base MiniERP puis charge les données de test (épisode 7).
# Exécuté par le service db-init de docker-compose, une fois SQL Server prêt.
set -euo pipefail

SQLCMD=/opt/mssql-tools18/bin/sqlcmd

for script in /database/01_schema.sql /database/02_seed.sql; do
  echo "Exécution de ${script}..."
  "${SQLCMD}" -S db -U sa -P "${MSSQL_SA_PASSWORD}" -C -b -i "${script}"
done

echo "Base MiniERP prête."
