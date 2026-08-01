CREATE TABLE IF NOT EXISTS uber_eats_orders (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_date  DATE            NOT NULL,
    restaurant  VARCHAR(255)    NOT NULL,
    amount      DECIMAL(10, 2)  NOT NULL,
    currency    VARCHAR(3)      NOT NULL DEFAULT 'CAD',
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_order_date (order_date),
    KEY idx_restaurant (restaurant),
    KEY idx_amount (amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
