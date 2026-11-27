
import sqlite3
import pandas as pd

DB = "data/raw/airtel.db"

conn = sqlite3.connect(DB)

def q(sql):
    return pd.read_sql_query(sql, conn)

print("\n1. JAN-JUN 2025 RECEIVED REVENUE")

print(q("""
SELECT
    COUNT(*) AS payment_count,
    SUM(amount_inr) AS received_revenue_inr
FROM recharges
WHERE recharge_date >= '2025-01-01'
AND recharge_date < '2025-07-01'
""").to_string(index=False))


print("\n2. REVENUE BY PLAN")

print(q("""
SELECT
    plan_name,
    COUNT(*) AS subscribers,
    ROUND(AVG(stated_arpu), 2) AS stated_arpu,
    ROUND(AVG(actual_arpu_6m), 2) AS actual_arpu,
    ROUND(AVG(arpu_gap), 2) AS average_gap
FROM customer_features
GROUP BY plan_name
ORDER BY actual_arpu DESC
""").to_string(index=False))


print("\n3. CONNECTION TYPE SHARE")

print(q("""
SELECT
    connection_type,
    COUNT(*) AS subscribers,
    ROUND(100.0 * COUNT(*) /
        SUM(COUNT(*)) OVER (), 2) AS subscriber_share,
    ROUND(100.0 * SUM(actual_arpu_6m) /
        SUM(SUM(actual_arpu_6m)) OVER (), 2) AS revenue_share
FROM customer_features
GROUP BY connection_type
""").to_string(index=False))


print("\n4. REVENUE BY DECILE")

print(q("""
WITH ranked AS (
    SELECT
        customer_id,
        recharge_total_6m,
        NTILE(10) OVER (
            ORDER BY recharge_total_6m DESC
        ) AS decile
    FROM customer_features
),
totals AS (
    SELECT
        decile,
        COUNT(*) AS subscribers,
        SUM(recharge_total_6m) AS revenue
    FROM ranked
    GROUP BY decile
)
SELECT
    decile,
    subscribers,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * revenue /
        SUM(revenue) OVER (), 2) AS revenue_share
FROM totals
ORDER BY decile
""").to_string(index=False))


conn.close()
