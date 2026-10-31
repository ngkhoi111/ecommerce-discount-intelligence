-- One first-observed shopper-product journey; all timestamps use source time.
CREATE OR REPLACE TABLE carts AS
SELECT DISTINCT client_id, sku, CAST(timestamp AS TIMESTAMP) AS ts
FROM read_parquet('{{RAW}}/add_to_cart.parquet');
CREATE OR REPLACE TABLE buys AS
SELECT DISTINCT client_id, sku, CAST(timestamp AS TIMESTAMP) AS ts
FROM read_parquet('{{RAW}}/product_buy.parquet');
CREATE OR REPLACE TABLE removals AS
SELECT DISTINCT client_id, sku, CAST(timestamp AS TIMESTAMP) AS ts
FROM read_parquet('{{RAW}}/remove_from_cart.parquet');

CREATE OR REPLACE TABLE first_carts AS
SELECT client_id, sku, min(ts) AS cart_time,
       min(ts) + INTERVAL '24 hours' AS decision_time
FROM carts GROUP BY client_id, sku;

-- Find the earliest observed purchase on or after the original cart.
CREATE OR REPLACE TABLE candidates AS
SELECT c.*, b.ts AS next_purchase
FROM first_carts c ASOF LEFT JOIN buys b
ON c.client_id = b.client_id AND c.sku = b.sku AND c.cart_time <= b.ts;

CREATE OR REPLACE TABLE cart_activity AS
SELECT f.client_id, f.sku, max(c.ts) AS last_cart,
       count(*) AS product_cart_events_24h
FROM first_carts f JOIN carts c USING (client_id, sku)
WHERE c.ts <= f.decision_time GROUP BY f.client_id, f.sku;

CREATE OR REPLACE TABLE candidates_with_state AS
SELECT c.*, a.product_cart_events_24h, a.last_cart, r.ts AS last_removal
FROM candidates c JOIN cart_activity a USING (client_id, sku)
ASOF LEFT JOIN removals r
ON c.client_id = r.client_id AND c.sku = r.sku AND c.decision_time >= r.ts;

-- Conservative common endpoint avoids claiming follow-up after any source ends.
CREATE OR REPLACE TABLE coverage AS
SELECT greatest((SELECT min(ts) FROM carts), (SELECT min(ts) FROM buys),
                (SELECT min(ts) FROM removals)) AS observation_start,
       least((SELECT max(ts) FROM carts), (SELECT max(ts) FROM buys),
             (SELECT max(ts) FROM removals)) AS observation_end;

CREATE OR REPLACE TABLE eligible AS
SELECT c.*,
       CAST(next_purchase > decision_time AND
            next_purchase <= decision_time + INTERVAL '7 days' AS INTEGER) AS label_raw,
       CASE WHEN next_purchase > decision_time AND
                 next_purchase <= decision_time + INTERVAL '7 days'
            THEN 1 ELSE 0 END AS purchased_7d
FROM candidates_with_state c CROSS JOIN coverage v
WHERE cart_time >= v.observation_start + INTERVAL '30 days'
  AND decision_time + INTERVAL '7 days' <= v.observation_end
  AND (next_purchase IS NULL OR next_purchase > decision_time)
  AND (last_removal IS NULL OR last_cart > last_removal);

-- Aggregate simultaneous events before cumulative windows to remove tie ambiguity.
CREATE OR REPLACE TABLE event_ticks AS
SELECT client_id, sku, ts, sum(cart_n) AS cart_n, sum(buy_n) AS buy_n
FROM (
  SELECT client_id, sku, ts, 1 AS cart_n, 0 AS buy_n FROM carts
  UNION ALL
  SELECT client_id, sku, ts, 0 AS cart_n, 1 AS buy_n FROM buys
) GROUP BY client_id, sku, ts;

CREATE OR REPLACE TABLE user_history AS
WITH ticks AS (
 SELECT client_id, ts, sum(cart_n) AS cart_n, sum(buy_n) AS buy_n
 FROM event_ticks GROUP BY client_id, ts
)
SELECT client_id, ts,
 sum(cart_n) OVER w AS user_cart_events,
 sum(buy_n) OVER w AS user_buy_events,
 min(ts) OVER w AS first_activity,
 max(CASE WHEN buy_n > 0 THEN ts END) OVER w AS last_buy
FROM ticks WINDOW w AS
 (PARTITION BY client_id ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);

CREATE OR REPLACE TABLE sku_history AS
WITH ticks AS (
 SELECT sku, ts, sum(cart_n) AS cart_n, sum(buy_n) AS buy_n
 FROM event_ticks GROUP BY sku, ts
)
SELECT sku, ts, sum(cart_n) OVER w AS sku_cart_events,
 sum(buy_n) OVER w AS sku_buy_events
FROM ticks WINDOW w AS
 (PARTITION BY sku ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);

CREATE OR REPLACE TABLE features AS
SELECT e.client_id, e.sku, e.cart_time, e.decision_time,
       e.decision_time + INTERVAL '7 days' AS outcome_end,
       e.next_purchase, e.purchased_7d, e.product_cart_events_24h,
       u.user_cart_events, u.user_buy_events,
       COALESCE(date_diff('second', u.last_buy, e.decision_time)/86400.0, 999.0) AS days_since_buy,
       date_diff('second', u.first_activity, e.decision_time)/86400.0 AS observed_history_days,
       s.sku_cart_events, s.sku_buy_events,
       extract(hour FROM e.decision_time) AS decision_hour,
       extract(dow FROM e.decision_time) AS decision_dow,
       CASE
         WHEN e.decision_time < TIMESTAMP '2022-09-15' AND
              e.decision_time + INTERVAL '7 days' < TIMESTAMP '2022-09-15' THEN 'train'
         WHEN e.decision_time >= TIMESTAMP '2022-09-15' AND
              e.decision_time + INTERVAL '7 days' < TIMESTAMP '2022-10-15' THEN 'validation'
         WHEN e.decision_time >= TIMESTAMP '2022-10-15' THEN 'test'
         ELSE 'purged'
       END AS split
FROM eligible e
ASOF LEFT JOIN user_history u
ON e.client_id = u.client_id AND e.decision_time >= u.ts
ASOF LEFT JOIN sku_history s
ON e.sku = s.sku AND e.decision_time >= s.ts;
