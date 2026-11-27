
import os
import sqlite3

folders = ["data"]

for folder in folders:
    print(f"\nSearching inside: {folder}")

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith((".db", ".sqlite", ".sqlite3")):

                path = os.path.join(root, file)
                print(f"\nDatabase found: {path}")

                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )

                    tables = cursor.fetchall()

                    for table in tables:
                        print("  Table:", table[0])

                    conn.close()

                except Exception as e:
                    print("  Error:", e)
