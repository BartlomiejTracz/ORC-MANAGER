import sqlite3

conn = sqlite3.connect("wrc_liga.db")
cursor = conn.cursor()

try:
    # Dodajemy informację o liczbie odcinków (domyślnie 7)
    cursor.execute("ALTER TABLE rallies ADD COLUMN stages_count INTEGER DEFAULT 7")
    conn.commit()
    print("✅ Pomyślnie dodano kolumnę liczby OS-ów do bazy!")
except sqlite3.OperationalError:
    print("⚠️ Kolumna już istnieje.")

conn.close()