# Architecture · Mini-ERP Analytics

Mise en place à l'épisode 6. L'application tient en trois conteneurs Docker, démarrés ensemble par `docker compose up`.

```text
Navigateur
   │  http://localhost:5173
   ▼
┌──────────────┐   /api/...   ┌──────────────┐    SQL    ┌──────────────┐
│ web          │ ───────────► │ api          │ ────────► │ db           │
│ React + Vite │              │ Python       │           │ SQL Server   │
│ port 5173    │              │ FastAPI      │           │ 2022         │
└──────────────┘              │ port 8000    │           │ port 1433    │
                              └──────────────┘           └──────────────┘
```

| Service | Rôle | Technologie | Port |
|---|---|---|---|
| `web` | L'interface affichée dans le navigateur | React, Vite | 5173 |
| `api` | Les règles métier et l'accès aux données | Python, FastAPI, SQLAlchemy, pilote ODBC 18 | 8000 |
| `db` | Les données : clients, produits, ventes, stock | SQL Server 2022 (édition Developer) | 1433 |
| `db-init` | Crée la base `MiniERP` et charge les données de test, puis s'arrête (épisode 7) | sqlcmd | – |

## Arborescence

```text
mini-erp-analytics/
├── docker-compose.yml      les trois services
├── .env.example            modèle des variables (copier en .env)
├── backend/                l'API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py         application FastAPI (dont /api/health)
│   │   ├── config.py       lecture des variables d'environnement
│   │   ├── database.py     connexion SQL Server, session par requête
│   │   ├── models.py       modèles SQLAlchemy (épisode 7)
│   │   ├── schemas.py      schémas Pydantic (épisode 8)
│   │   └── routers/        routes /api/clients et /api/produits (épisode 8)
│   └── tests/              tests pytest (base SQLite en mémoire)
├── frontend/               l'interface
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js      proxy /api vers l'API
│   └── src/
│       ├── main.jsx
│       └── App.jsx         page d'accueil : état de l'API et de la base
├── database/               scripts SQL (épisode 7)
│   ├── 01_schema.sql
│   ├── 02_seed.sql
│   └── init.sh
├── docs/
└── prompts/
```

## Décisions

| Décision | Pourquoi |
|---|---|
| Un conteneur par brique | Chaque brique se lance, se teste et se remplace séparément. |
| Secrets dans `.env`, jamais dans le code | Le fichier `.env` est exclu par `.gitignore` ; seul `.env.example` est partagé. |
| Contrôle de santé sur SQL Server | L'API ne démarre qu'une fois la base prête (`depends_on: condition: service_healthy`). |
| Route `/api/health` | Vérifie en un appel que l'API répond et que la base est joignable (503 sinon). |
| Proxy `/api` dans Vite | L'interface appelle l'API sans souci de CORS pendant le développement. |
