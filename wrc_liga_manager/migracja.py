import sqlite3

conn = sqlite3.connect("wrc_liga.db")
cursor = conn.cursor()

try:
    # Dodajemy nową kolumnę na kolor ramki do tabeli teams
    cursor.execute("ALTER TABLE teams ADD COLUMN color_border_hex TEXT DEFAULT '#000000'")
    conn.commit()
    print("✅ Pomyślnie zaktualizowano bazę danych o kolumnę ramki (color_border_hex)!")
except sqlite3.OperationalError:
    print("⚠️ Kolumna już istnieje lub wystąpił błąd.")

conn.close()