# db_query.py

import psycopg2
import config

def fetch_all_prices():
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )

        cur = conn.cursor()

        cur.execute("SELECT * FROM prices;")
        rows = cur.fetchall()

        for row in rows:
            print(row)
    
    except Exception as e:
        print("Query failed", e)

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

fetch_all_prices()