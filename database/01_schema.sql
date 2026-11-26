-- Mini-ERP Analytics · schéma de la base (épisode 7, table utilisateurs : épisode 10)
-- Relançable sans erreur : chaque objet n'est créé que s'il n'existe pas encore.

IF DB_ID(N'MiniERP') IS NULL
    CREATE DATABASE MiniERP;
GO

USE MiniERP;
GO

-- Clients ---------------------------------------------------------------
IF OBJECT_ID(N'dbo.clients', N'U') IS NULL
CREATE TABLE dbo.clients (
    id          INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_clients PRIMARY KEY,
    nom         NVARCHAR(120) NOT NULL,
    email       NVARCHAR(254) NOT NULL CONSTRAINT uq_clients_email UNIQUE
                CONSTRAINT ck_clients_email CHECK (email LIKE N'%_@_%._%'),
    numero_tva  NVARCHAR(20)  NOT NULL CONSTRAINT uq_clients_tva UNIQUE,
    ville       NVARCHAR(80)  NULL,
    cree_le     DATETIME2(0)  NOT NULL CONSTRAINT df_clients_cree_le DEFAULT SYSUTCDATETIME()
);
GO

-- Produits --------------------------------------------------------------
IF OBJECT_ID(N'dbo.produits', N'U') IS NULL
CREATE TABLE dbo.produits (
    id            INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_produits PRIMARY KEY,
    reference     NVARCHAR(30)  NOT NULL CONSTRAINT uq_produits_reference UNIQUE,
    nom           NVARCHAR(150) NOT NULL,
    categorie     NVARCHAR(60)  NOT NULL,
    prix_ht       DECIMAL(12, 2) NOT NULL CONSTRAINT ck_produits_prix CHECK (prix_ht >= 0),
    taux_tva      DECIMAL(5, 2)  NOT NULL CONSTRAINT df_produits_tva DEFAULT 20.00
                  CONSTRAINT ck_produits_tva CHECK (taux_tva BETWEEN 0 AND 100),
    stock_actuel  INT NOT NULL CONSTRAINT df_produits_stock DEFAULT 0
                  CONSTRAINT ck_produits_stock CHECK (stock_actuel >= 0),
    seuil_alerte  INT NOT NULL CONSTRAINT df_produits_seuil DEFAULT 5
                  CONSTRAINT ck_produits_seuil CHECK (seuil_alerte >= 0),
    actif         BIT NOT NULL CONSTRAINT df_produits_actif DEFAULT 1
);
GO

-- Ventes ----------------------------------------------------------------
IF OBJECT_ID(N'dbo.ventes', N'U') IS NULL
CREATE TABLE dbo.ventes (
    id          INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_ventes PRIMARY KEY,
    numero      NVARCHAR(20) NOT NULL CONSTRAINT uq_ventes_numero UNIQUE,
    client_id   INT NOT NULL CONSTRAINT fk_ventes_client REFERENCES dbo.clients (id),
    date_vente  DATETIME2(0) NOT NULL CONSTRAINT df_ventes_date DEFAULT SYSUTCDATETIME(),
    statut      NVARCHAR(12) NOT NULL CONSTRAINT df_ventes_statut DEFAULT N'brouillon'
                CONSTRAINT ck_ventes_statut CHECK (statut IN (N'brouillon', N'validee', N'annulee')),
    total_ht    DECIMAL(14, 2) NOT NULL CONSTRAINT df_ventes_ht DEFAULT 0 CONSTRAINT ck_ventes_ht CHECK (total_ht >= 0),
    total_tva   DECIMAL(14, 2) NOT NULL CONSTRAINT df_ventes_tva DEFAULT 0 CONSTRAINT ck_ventes_tva CHECK (total_tva >= 0),
    total_ttc   DECIMAL(14, 2) NOT NULL CONSTRAINT df_ventes_ttc DEFAULT 0 CONSTRAINT ck_ventes_ttc CHECK (total_ttc >= 0)
);
GO

-- Lignes de vente -------------------------------------------------------
IF OBJECT_ID(N'dbo.lignes_vente', N'U') IS NULL
CREATE TABLE dbo.lignes_vente (
    id                INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_lignes_vente PRIMARY KEY,
    vente_id          INT NOT NULL CONSTRAINT fk_lignes_vente_vente REFERENCES dbo.ventes (id) ON DELETE CASCADE,
    produit_id        INT NOT NULL CONSTRAINT fk_lignes_vente_produit REFERENCES dbo.produits (id),
    quantite          INT NOT NULL CONSTRAINT ck_lignes_vente_quantite CHECK (quantite > 0),
    prix_unitaire_ht  DECIMAL(12, 2) NOT NULL CONSTRAINT ck_lignes_vente_prix CHECK (prix_unitaire_ht >= 0),
    taux_tva          DECIMAL(5, 2)  NOT NULL CONSTRAINT ck_lignes_vente_tva CHECK (taux_tva BETWEEN 0 AND 100),
    CONSTRAINT uq_lignes_vente_produit UNIQUE (vente_id, produit_id)
);
GO

-- Mouvements de stock ---------------------------------------------------
IF OBJECT_ID(N'dbo.mouvements_stock', N'U') IS NULL
CREATE TABLE dbo.mouvements_stock (
    id              INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_mouvements_stock PRIMARY KEY,
    produit_id      INT NOT NULL CONSTRAINT fk_mouvements_produit REFERENCES dbo.produits (id),
    type_mouvement  NVARCHAR(10) NOT NULL CONSTRAINT ck_mouvements_type CHECK (type_mouvement IN (N'entree', N'sortie')),
    quantite        INT NOT NULL CONSTRAINT ck_mouvements_quantite CHECK (quantite > 0),
    date_mouvement  DATETIME2(0) NOT NULL CONSTRAINT df_mouvements_date DEFAULT SYSUTCDATETIME(),
    vente_id        INT NULL CONSTRAINT fk_mouvements_vente REFERENCES dbo.ventes (id),
    commentaire     NVARCHAR(200) NULL
);
GO

-- Utilisateurs (épisode 10) ---------------------------------------------
-- Aucun mot de passe en clair : seulement son empreinte scrypt. Aucun compte n'est créé ici :
-- le premier administrateur se crée avec  docker compose exec api python -m app.creer_admin
IF OBJECT_ID(N'dbo.utilisateurs', N'U') IS NULL
CREATE TABLE dbo.utilisateurs (
    id                  INT IDENTITY(1, 1) NOT NULL CONSTRAINT pk_utilisateurs PRIMARY KEY,
    email               NVARCHAR(254) NOT NULL CONSTRAINT uq_utilisateurs_email UNIQUE
                        CONSTRAINT ck_utilisateurs_email CHECK (email LIKE N'%_@_%._%'),
    nom                 NVARCHAR(120) NOT NULL,
    mot_de_passe_hache  VARCHAR(255)  NOT NULL,
    role                NVARCHAR(20)  NOT NULL
                        CONSTRAINT ck_utilisateurs_role CHECK (role IN (N'commercial', N'vendeur', N'magasinier',
                                                                         N'manager', N'dirigeant', N'administrateur')),
    actif               BIT NOT NULL CONSTRAINT df_utilisateurs_actif DEFAULT 1,
    cree_le             DATETIME2(0) NOT NULL CONSTRAINT df_utilisateurs_cree_le DEFAULT SYSUTCDATETIME()
);
GO

-- Index sur les colonnes filtrées ou jointes souvent --------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_ventes_date' AND object_id = OBJECT_ID(N'dbo.ventes'))
    CREATE INDEX ix_ventes_date ON dbo.ventes (date_vente) INCLUDE (statut, total_ht);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_ventes_client' AND object_id = OBJECT_ID(N'dbo.ventes'))
    CREATE INDEX ix_ventes_client ON dbo.ventes (client_id);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_lignes_vente_produit' AND object_id = OBJECT_ID(N'dbo.lignes_vente'))
    CREATE INDEX ix_lignes_vente_produit ON dbo.lignes_vente (produit_id);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'ix_mouvements_produit_date' AND object_id = OBJECT_ID(N'dbo.mouvements_stock'))
    CREATE INDEX ix_mouvements_produit_date ON dbo.mouvements_stock (produit_id, date_mouvement);
GO
