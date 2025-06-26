# db_setup.py

import psycopg2
import config

try:
    conn = psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT
    )

    print("Connected to:", conn.get_dsn_parameters())

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            price NUMERIC NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    conn.commit()
    print("Table created successfully.")

except Exception as e:
    print("Error:", e)

finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()