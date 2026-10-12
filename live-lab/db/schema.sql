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

/* ---------- corrugator-plant customers ---------- */
IF OBJECT_ID('dbo.Customers') IS NOT NULL DROP TABLE dbo.Customers;
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
    (1,'rockford_ap','09a3...replace_with_real_hash...', 0),
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
/* [VULN] OrderDesk connects as a login in the db_owner role - far more than it
   needs (it only reads/writes a few tables). Lesson: least privilege. The fix
   creates an app login with only the needed grants, and never enables
   xp_cmdshell. Over-privilege is what turns one SQLi into full host takeover. */

PRINT 'millops ready. Intentional weaknesses are tagged [VULN] - find them, then fix them.';
GO
