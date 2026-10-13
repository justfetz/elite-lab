/* =====================================================================
   millops - the Lakefront Paper & Container Co. sample database
   A "Northwind for security": a small, realistic SQL Server schema with
   seed data, for the elite-lab live lab.

   *** TRAINING ONLY - CONTAINS INTENTIONAL WEAKNESSES ***
   Some objects here are deliberately insecure so you can FIND and FIX them.
   Each is tagged  -- [VULN]  with the lesson. Never ship anything like this.

   Run against a LOCAL SQL Server you own (Developer edition / the official
   Docker image). See live-lab/README.md.
   ===================================================================== */

IF DB_ID('millops') IS NULL CREATE DATABASE millops;
GO
USE millops;
GO

/* ---------- clean drop in child -> parent order (so re-running never fails on
             a foreign key). Must come BEFORE any create. ---------- */
IF OBJECT_ID('dbo.Shipments') IS NOT NULL DROP TABLE dbo.Shipments;
IF OBJECT_ID('dbo.Orders')    IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Users')     IS NOT NULL DROP TABLE dbo.Users;
IF OBJECT_ID('dbo.Trucks')    IS NOT NULL DROP TABLE dbo.Trucks;
IF OBJECT_ID('dbo.Customers') IS NOT NULL DROP TABLE dbo.Customers;
GO

/* ---------- corrugator-plant customers ---------- */
CREATE TABLE dbo.Customers (
    CustomerId   INT IDENTITY PRIMARY KEY,
    PlantName    NVARCHAR(100) NOT NULL,   -- e.g. 'Rockford Corrugated'
    City         NVARCHAR(60),
    CreditHold   BIT NOT NULL DEFAULT 0
);

/* ---------- portal logins (OrderDesk) ---------- */
IF OBJECT_ID('dbo.Users') IS NOT NULL DROP TABLE dbo.Users;
CREATE TABLE dbo.Users (
    UserId       INT IDENTITY PRIMARY KEY,
    CustomerId   INT NOT NULL REFERENCES dbo.Customers(CustomerId),
    Username     NVARCHAR(60) NOT NULL UNIQUE,
    -- [VULN] passwords are stored as unsalted SHA-256 hex. Lesson: salting +
    -- a slow KDF (bcrypt/argon2). crack-01 shows why unsalted fast hashes fall.
    PwHash       CHAR(64) NOT NULL,
    IsAdmin      BIT NOT NULL DEFAULT 0
);

/* ---------- orders, trucks, shipments ---------- */
IF OBJECT_ID('dbo.Orders') IS NOT NULL DROP TABLE dbo.Orders;
CREATE TABLE dbo.Orders (
    OrderId      INT IDENTITY(1000,1) PRIMARY KEY,
    CustomerId   INT NOT NULL REFERENCES dbo.Customers(CustomerId),
    PaperGrade   NVARCHAR(30) NOT NULL,     -- e.g. '26# kraft linerboard'
    Rolls        INT NOT NULL,
    WeightLbs    INT NOT NULL,
    Status       NVARCHAR(20) NOT NULL DEFAULT 'received',  -- received/released/loaded/shipped
    CreatedAt    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

IF OBJECT_ID('dbo.Trucks') IS NOT NULL DROP TABLE dbo.Trucks;
CREATE TABLE dbo.Trucks (
    TruckId      INT IDENTITY PRIMARY KEY,
    Plate        NVARCHAR(12) NOT NULL,
    MaxWeightLbs INT NOT NULL              -- LoadMaster packs by weight up to this
);

IF OBJECT_ID('dbo.Shipments') IS NOT NULL DROP TABLE dbo.Shipments;
CREATE TABLE dbo.Shipments (
    ShipmentId   INT IDENTITY PRIMARY KEY,
    OrderId      INT NOT NULL REFERENCES dbo.Orders(OrderId),
    TruckId      INT NOT NULL REFERENCES dbo.Trucks(TruckId),
    ShippedAt    DATETIME2 NULL
);
GO

/* ---------- seed data ---------- */
INSERT dbo.Customers (PlantName, City) VALUES
    ('Rockford Corrugated','Rockford'),
    ('Gary Container Works','Gary'),
    ('Milwaukee Box Co','Milwaukee');

-- demo logins. PwHash = SHA-256 of the password (unsalted - see [VULN] above).
-- 'autumn2024'  -> for the Rockford user;  'admin'  -> the weak admin password.
INSERT dbo.Users (CustomerId, Username, PwHash, IsAdmin) VALUES
    (1,'rockford_ap','20946a2fb2c13f9dd77b36428e41755ff7a2c5d267eb7c27f2dcffcbd63a8f12', 0),  -- 'autumn2024'
    (1,'millops_admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 1);

INSERT dbo.Orders (CustomerId, PaperGrade, Rolls, WeightLbs, Status) VALUES
    (1,'26# kraft linerboard', 40, 48000, 'received'),
    (2,'42# medium',           60, 51000, 'released'),
    (1,'35# linerboard',       25, 30000, 'shipped');

INSERT dbo.Trucks (Plate, MaxWeightLbs) VALUES ('IL-4471X',52000),('IL-8820Q',48000);
GO

/* ---------- OrderDesk's order-tracking proc ---------- */
/* [VULN] This builds SQL by string concatenation, so a crafted order number
   injects. Lesson (app-01): parameterize. The FIX version uses @OrderId as a
   real parameter with sp_executesql. Try tracking:  1000  then:  1000 OR 1=1   */
IF OBJECT_ID('dbo.sp_TrackOrder') IS NOT NULL DROP PROCEDURE dbo.sp_TrackOrder;
GO
CREATE PROCEDURE dbo.sp_TrackOrder @OrderNo NVARCHAR(50)
AS
BEGIN
    DECLARE @sql NVARCHAR(MAX) =
        'SELECT OrderId, PaperGrade, Rolls, WeightLbs, Status
           FROM dbo.Orders WHERE OrderId = ' + @OrderNo + ';';   -- [VULN] injectable
    EXEC (@sql);
END
GO

/* ---------- the application login ---------- */
/* [VULN] OrderDesk connects as an OVER-PRIVILEGED login: db_owner, far more than
   it needs (it only reads/writes a few tables). This is what turns one SQLi into
   full database - and often host - takeover. The login is actually created here so
   the weakness is runnable, not just described. */
IF SUSER_ID('orderdesk_app') IS NULL
    CREATE LOGIN orderdesk_app WITH PASSWORD = 'Ch4ngeMe_demo!';
IF USER_ID('orderdesk_app') IS NULL
    CREATE USER orderdesk_app FOR LOGIN orderdesk_app;
ALTER ROLE db_owner ADD MEMBER orderdesk_app;     -- [VULN] the over-grant
GO

/* The FIX (least privilege): drop it from db_owner and grant ONLY what the app
   uses. Uncomment to apply, then point OrderDesk at this login:
     ALTER ROLE db_owner DROP MEMBER orderdesk_app;
     GRANT SELECT, INSERT, UPDATE ON dbo.Orders    TO orderdesk_app;
     GRANT SELECT               ON dbo.Customers TO orderdesk_app;
     GRANT SELECT               ON dbo.Users     TO orderdesk_app;
   -- and never: EXEC sp_configure 'xp_cmdshell', 1;  (leave it OFF) */

PRINT 'millops ready. Intentional weaknesses are tagged [VULN] - find them, then fix them.';
GO
