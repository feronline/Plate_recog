import os
import psycopg2
import csv
conn = psycopg2.connect(
    dbname="railway",  # Railway'de verdiğiniz veritabanı adı
    user="postgres",
    password="axKfBzyEDoOigbkcRShuLiGquuqochjf",
    host="centerbeam.proxy.rlwy.net",
    port="24995",
    sslmode="require"  # SSL ile bağlantı zorunluysa SSL modu
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
    SELECT marka, ARRAY_AGG(DISTINCT model ORDER BY model) AS modeller
    FROM vehicle_emissions
    GROUP BY marka
    ORDER BY marka;
""")
rows = cur.fetchall()

for marka, modeller in rows:
    print(f"{marka}: {', '.join(modeller)}")

cur.close()
conn.close()