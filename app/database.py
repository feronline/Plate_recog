import psycopg2

conn = psycopg2.connect("postgresql://postgres:axKfBzyEDoOigbkcRShuLiGquuqochjf@centerbeam.proxy.rlwy.net:24995/railway")

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS vehicles (
    plaka TEXT PRIMARY KEY,
    marka TEXT NOT NULL,
    model TEXT NOT NULL,
    renk TEXT NOT NULL,
    yakit_turu TEXT NOT NULL,
    arac_tipi TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS vehicle_emissions (
    marka TEXT NOT NULL,
    model TEXT NOT NULL,
    yil INTEGER NOT NULL,
    yakit_turu TEXT NOT NULL,
    arac_tipi TEXT NOT NULL,
    karbon_emisyon REAL NOT NULL
);
""")

conn.commit()
cur.close()
conn.close()

print("Done.")
