# n8n workflows

## `crypto-prices-to-mysql.json`

Scheduled workflow that fetches crypto prices from CoinGecko every hour and
upserts them into a MySQL table.

### Flow

1. **Schedule Trigger** – fires every 1 hour.
2. **HTTP Request** – `GET https://api.coingecko.com/api/v3/simple/price` for
   `bitcoin, ethereum, solana, cardano` in USD, including market cap, 24h
   volume, 24h change, and last-updated timestamp.
3. **Code (JS)** – flattens the `{ coin: { usd: ... } }` response shape into
   one item per coin with normalized field names.
4. **MySQL** – `INSERT ... ON DUPLICATE KEY UPDATE` against `crypto_prices`,
   keyed on `coin_id`.

### Target table

Create the destination table once before activating the workflow:

```sql
CREATE TABLE crypto_prices (
  coin_id           VARCHAR(64)     NOT NULL PRIMARY KEY,
  price_usd         DECIMAL(24, 8),
  market_cap_usd    DECIMAL(24, 2),
  volume_24h_usd    DECIMAL(24, 2),
  change_24h_pct    DECIMAL(10, 4),
  source_updated_at DATETIME,
  fetched_at        DATETIME        NOT NULL
);
```

If you want full history instead of latest-per-coin, drop the `PRIMARY KEY` on
`coin_id`, add an `AUTO_INCREMENT id`, and change the MySQL node to a plain
`INSERT` (remove the `ON DUPLICATE KEY UPDATE` clause).

### Import

1. In n8n: **Workflows -> Import from File** -> select
   `n8n/crypto-prices-to-mysql.json`.
2. Open the **Upsert into MySQL** node and bind it to your MySQL credential
   (the imported `credentials.id` is a placeholder).
3. Run once manually to verify, then toggle **Active**.

### Notes

- CoinGecko's free tier is rate-limited; hourly is well within limits. Add an
  API key header in the HTTP node if you hit `429`s.
- Adjust the `ids` query parameter to track different coins.
- Timezone is set to UTC in workflow settings so the schedule is stable across
  DST changes.
