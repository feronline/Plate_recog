import sqlite3

# Veritabanı bağlantısı oluştur (dosya olarak 'veritabani.db')
conn = sqlite3.connect('veritabani.db')
cursor = conn.cursor()

# Tablo oluştur
cursor.execute('''
CREATE TABLE IF NOT EXISTS araclar (
    plaka TEXT PRIMARY KEY,
    marka TEXT NOT NULL,
    model TEXT NOT NULL,
    yakit_turu TEXT NOT NULL,
    arac_yili INTEGER NOT NULL
)
''')

# Değişiklikleri kaydet ve bağlantıyı kapat
conn.commit()
conn.close()

print("Tablo başarıyla oluşturuldu.")