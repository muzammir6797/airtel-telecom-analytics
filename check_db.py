
import sqlite3

db_path = "data/raw/airtel.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = [
    "circles",
    "plans",
    "customers",
    "usage_daily",
    "recharges",
    "complaints",
    "customer_features"
]

for table in tables:
    print("\n" + "=" * 50)
    print("TABLE:", table)
    print("=" * 50)

    cursor.execute(f"PRAGMA table_info({table})")

    columns = cursor.fetchall()

    for column in columns:
        print(
            f"Column: {column[1]:25} "
            f"Type: {column[2]}"
        )

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]

    print("Total records:", count)

conn.close()
