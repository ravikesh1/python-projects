-- Sample data for the demo schema (schema/schema.sql).
-- Load after schema.sql:
--   mysql -h <host> -u <user> -p <database> < schema/seed.sql
--
-- Inserts use explicit ids so foreign keys line up regardless of AUTO_INCREMENT
-- state. Safe to re-run on a fresh database; re-running on a populated one will
-- collide on primary keys.

INSERT INTO users (id, email, name, created_at) VALUES
    (1, 'ada@example.com',    'Ada Lovelace',   '2025-11-01 09:00:00'),
    (2, 'alan@example.com',   'Alan Turing',    '2025-12-15 14:30:00'),
    (3, 'grace@example.com',  'Grace Hopper',   '2026-01-20 11:15:00');

INSERT INTO products (id, name, price, created_at) VALUES
    (1, 'Mechanical Keyboard', 89.99,  '2025-10-01 08:00:00'),
    (2, 'USB-C Cable',          12.50,  '2025-10-01 08:00:00'),
    (3, '27" Monitor',         249.00, '2025-10-05 08:00:00');

INSERT INTO orders (id, user_id, status, total_amount, created_at) VALUES
    (1, 1, 'paid',    102.49, '2025-12-20 10:00:00'),
    (2, 2, 'pending', 249.00, '2026-02-10 16:45:00'),
    (3, 1, 'paid',     25.00, '2026-03-02 12:30:00');

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1, 89.99),
    (2, 1, 2, 1, 12.50),
    (3, 2, 3, 1, 249.00),
    (4, 3, 2, 2, 12.50);
