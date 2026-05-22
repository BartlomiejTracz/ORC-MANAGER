import sqlite3

def init_db():
    conn = sqlite3.connect("wrc_liga.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS championships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        champ_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        car TEXT NOT NULL,
        color_hex TEXT DEFAULT '#FFFFFF',
        color_border_hex TEXT DEFAULT '#000000',
        FOREIGN KEY (champ_id) REFERENCES championships (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        champ_id INTEGER NOT NULL,
        discord_name TEXT NOT NULL,
        ea_nickname TEXT NOT NULL,
        team_id INTEGER,
        nationality TEXT DEFAULT '🏳️',
        number INTEGER,
        platform TEXT,
        FOREIGN KEY (champ_id) REFERENCES championships (id) ON DELETE CASCADE,
        FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS rallies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        champ_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        stages_count INTEGER DEFAULT 7,
        FOREIGN KEY (champ_id) REFERENCES championships (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS stage_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rally_id INTEGER NOT NULL,
        driver_id INTEGER NOT NULL,
        stage_number INTEGER NOT NULL,
        time_ms INTEGER NOT NULL,
        stage_rank INTEGER DEFAULT 999,
        FOREIGN KEY (rally_id) REFERENCES rallies (id) ON DELETE CASCADE,
        FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Successfully created the database with Nationality, Number, and Platform columns!")

if __name__ == "__main__":
    init_db()