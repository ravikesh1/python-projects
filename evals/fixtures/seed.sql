-- Seed schema and data for the MySQL MCP server eval suite.
-- Loaded directly via PyMySQL (not through the MCP tools) so it works regardless
-- of the server's MYSQL_ALLOW_WRITE / MYSQL_ALLOW_DDL flags.
--
-- The eval database name is substituted by the harness (see harness.py); the
-- `{db}` placeholder below is replaced before execution.

DROP DATABASE IF EXISTS `{db}`;
CREATE DATABASE `{db}` CHARACTER SET utf8mb4;
USE `{db}`;

CREATE TABLE users (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    name       VARCHAR(100)  NOT NULL,
    email      VARCHAR(255)  NOT NULL,
    created_at DATE          NOT NULL,
    balance    DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    active     TINYINT(1)    NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE orders (
    id      INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT           NOT NULL,
    amount  DECIMAL(10,2) NOT NULL,
    payload BLOB
) ENGINE=InnoDB;

-- Three known users used for exact-value assertions.
INSERT INTO users (id, name, email, created_at, balance, active) VALUES
    (1, 'Alice',   'alice@example.com',   '2024-01-15', 100.50, 1),
    (2, 'Bob',     'bob@example.com',     '2024-02-20',   0.00, 0),
    (3, 'Charlie', 'charlie@example.com', '2024-03-25',  42.75, 1);

-- Filler users (ids 4..22) so a 5-row limit reliably truncates.
INSERT INTO users (name, email, created_at, balance, active) VALUES
    ('user04', 'user04@example.com', '2024-04-01', 1.00, 1),
    ('user05', 'user05@example.com', '2024-04-02', 1.00, 1),
    ('user06', 'user06@example.com', '2024-04-03', 1.00, 1),
    ('user07', 'user07@example.com', '2024-04-04', 1.00, 1),
    ('user08', 'user08@example.com', '2024-04-05', 1.00, 1),
    ('user09', 'user09@example.com', '2024-04-06', 1.00, 1),
    ('user10', 'user10@example.com', '2024-04-07', 1.00, 1),
    ('user11', 'user11@example.com', '2024-04-08', 1.00, 1),
    ('user12', 'user12@example.com', '2024-04-09', 1.00, 1),
    ('user13', 'user13@example.com', '2024-04-10', 1.00, 1),
    ('user14', 'user14@example.com', '2024-04-11', 1.00, 1),
    ('user15', 'user15@example.com', '2024-04-12', 1.00, 1),
    ('user16', 'user16@example.com', '2024-04-13', 1.00, 1),
    ('user17', 'user17@example.com', '2024-04-14', 1.00, 1),
    ('user18', 'user18@example.com', '2024-04-15', 1.00, 1),
    ('user19', 'user19@example.com', '2024-04-16', 1.00, 1),
    ('user20', 'user20@example.com', '2024-04-17', 1.00, 1),
    ('user21', 'user21@example.com', '2024-04-18', 1.00, 1),
    ('user22', 'user22@example.com', '2024-04-19', 1.00, 1);

-- Orders exercising Decimal + BLOB (bytes) serialization.
-- The payload for order 1 is valid UTF-8 ("hello"); order 2 is non-UTF-8 bytes
-- so the server must fall back to a hex encoding.
INSERT INTO orders (id, user_id, amount, payload) VALUES
    (1, 1, 19.99, _binary 'hello'),
    (2, 1, 5.00,  _binary X'00FF00FF'),
    (3, 3, 12.34, NULL);
