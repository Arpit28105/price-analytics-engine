-- 1. Drop existing view if it exists
DROP VIEW IF EXISTS v_product_price_impact;

-- 2. Create the Analytical View using Window Functions
CREATE OR REPLACE VIEW v_product_price_impact AS
WITH price_changes AS (
    SELECT
        product_id,
        product_name,
        price AS current_price,
        valid_from,
        valid_to,
        LAG(price) OVER (
            PARTITION BY product_id
            ORDER BY valid_from
        ) AS previous_price,
        ROUND(
            (price - LAG(price) OVER (PARTITION BY product_id ORDER BY valid_from))
            / NULLIF(LAG(price) OVER (PARTITION BY product_id ORDER BY valid_from), 0) * 100,
            2
        ) AS pct_price_change
    FROM dim_product
),

sales_daily_velocity AS (
    SELECT
        product_id,
        sale_date,
        quantity_sold,
        ROUND(
            AVG(quantity_sold) OVER (
                PARTITION BY product_id
                ORDER BY sale_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ),
            2
        ) AS avg_7_day_sales
    FROM fact_sales
),

sales_impact AS (
    SELECT
        s.product_id,
        s.sale_date,
        s.quantity_sold,
        s.avg_7_day_sales,
        LAG(s.avg_7_day_sales, 7) OVER (
            PARTITION BY s.product_id
            ORDER BY s.sale_date
        ) AS prev_7_day_sales
    FROM sales_daily_velocity s
)

SELECT
    p.product_id,
    p.product_name,
    p.previous_price,
    p.current_price,
    p.pct_price_change,
    p.valid_from AS price_hike_date,
    s.quantity_sold AS sales_on_hike_day,
    s.avg_7_day_sales AS post_hike_avg_sales,
    s.prev_7_day_sales AS pre_hike_avg_sales,
    ROUND(
        (s.avg_7_day_sales - s.prev_7_day_sales)
        / NULLIF(s.prev_7_day_sales, 0) * 100,
        2
    ) AS pct_sales_volume_change,
    CASE
        WHEN p.pct_price_change > 10 AND s.avg_7_day_sales < s.prev_7_day_sales
        THEN 'HIGH RISK (ELASTIC DROP)'
        WHEN p.pct_price_change > 0 AND s.avg_7_day_sales >= s.prev_7_day_sales
        THEN 'INELASTIC (HEALTHY HIKE)'
        ELSE 'NORMAL VARIATION'
    END AS elasticity_flag
FROM price_changes p
JOIN sales_impact s
    ON p.product_id = s.product_id
   AND p.valid_from = s.sale_date
WHERE p.previous_price IS NOT NULL;