import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def log_vehicle_to_db(plate, entry_time, exit_time, total_time_s, parked_time_s, moving_time_s):
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT karbon_emisyon FROM vehicles WHERE plaka = %s", (plate,))
        result = cur.fetchone()
        if result is None or result[0] is None:
            print(f"{plate} plakalı araç için emisyon değeri yok.")
            return

        emission_rate_per_km = result[0]
        moving_minutes = moving_time_s / 60
        distance_km = 0.5 * moving_minutes
        carbon_emission = distance_km * emission_rate_per_km

        cur.execute("""
            INSERT INTO vehicle_logs (
                plate, entry_time, exit_time,
                total_time_seconds, total_parked_seconds,
                actual_moving_seconds, carbon_emission
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (plate) DO UPDATE SET
                entry_time = EXCLUDED.entry_time,
                exit_time = EXCLUDED.exit_time,
                total_time_seconds = EXCLUDED.total_time_seconds,
                total_parked_seconds = EXCLUDED.total_parked_seconds,
                actual_moving_seconds = EXCLUDED.actual_moving_seconds,
                carbon_emission = EXCLUDED.carbon_emission
        """, (
            plate, entry_time, exit_time,
            total_time_s, parked_time_s, moving_time_s,
            carbon_emission
        ))

        cur.close()
        conn.close()
        print(f"✅ {plate} için {carbon_emission:.2f} gram CO₂ veritabanına eklendi.")

    except Exception as e:
        print(f"❌ DB Hatası: {e}")

