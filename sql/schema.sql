-- ============================================================
-- Automotive Sales ETL Pipeline - Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS automotive_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE automotive_db;

-- ------------------------------------------------------------
-- Table: brands
-- Stores car manufacturer information
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS brands (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    country     VARCHAR(100),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: vehicles
-- Stores vehicle specifications and pricing
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id      INT NOT NULL UNIQUE,
    brand_id        INT NOT NULL,
    model           VARCHAR(100) NOT NULL,
    year            INT NOT NULL,
    category        VARCHAR(50),          -- Sedan, SUV, Truck, Coupe
    fuel_type       VARCHAR(50),          -- Gasoline, Diesel, Electric, Hybrid
    transmission    VARCHAR(50),          -- Manual, Automatic, CVT
    engine_size     DECIMAL(4,1),         -- in litres, 0.0 for EVs
    horsepower      INT,
    mpg_city        DECIMAL(5,2),
    mpg_highway     DECIMAL(5,2),
    mpg_combined    DECIMAL(5,2),
    base_price      DECIMAL(10,2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- Table: sales
-- Stores individual sales transactions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sale_id         INT NOT NULL UNIQUE,
    vehicle_id      INT NOT NULL,
    sale_date       DATE NOT NULL,
    sale_price      DECIMAL(10,2) NOT NULL,
    dealer_city     VARCHAR(100),
    dealer_state    VARCHAR(50),
    customer_type   VARCHAR(50),          -- Individual, Fleet, Corporate
    color           VARCHAR(50),
    mileage         INT DEFAULT 0,
    discount_amount DECIMAL(10,2),
    discount_pct    DECIMAL(5,2),
    sale_year       INT,
    sale_month      INT,
    sale_quarter    INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- Table: etl_logs
-- Tracks each ETL pipeline run
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etl_logs (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    run_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_extracted   INT DEFAULT 0,
    records_transformed INT DEFAULT 0,
    records_loaded      INT DEFAULT 0,
    status              VARCHAR(20) NOT NULL,     -- SUCCESS, FAILED
    message             TEXT
);

-- ------------------------------------------------------------
-- Useful views for analytics
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_sales_with_details AS
SELECT
    s.sale_id,
    s.sale_date,
    s.sale_price,
    s.discount_pct,
    s.dealer_city,
    s.dealer_state,
    s.customer_type,
    s.color,
    s.sale_year,
    s.sale_month,
    s.sale_quarter,
    v.vehicle_id,
    v.model,
    v.year   AS model_year,
    v.category,
    v.fuel_type,
    v.transmission,
    v.mpg_combined,
    v.base_price,
    b.name   AS brand,
    b.country AS brand_country
FROM sales s
JOIN vehicles v ON s.vehicle_id = v.vehicle_id
JOIN brands  b ON v.brand_id   = b.id;

CREATE OR REPLACE VIEW vw_brand_summary AS
SELECT
    b.name               AS brand,
    b.country,
    COUNT(s.sale_id)     AS total_sales,
    SUM(s.sale_price)    AS total_revenue,
    AVG(s.sale_price)    AS avg_sale_price,
    AVG(s.discount_pct)  AS avg_discount_pct
FROM brands b
JOIN vehicles v ON b.id = v.brand_id
JOIN sales    s ON v.vehicle_id = s.vehicle_id
GROUP BY b.id, b.name, b.country;
