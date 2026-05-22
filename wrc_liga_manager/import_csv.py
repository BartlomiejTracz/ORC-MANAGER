import pandas as pd
import sqlite3

def racenet_time_to_ms(time_str):
    """Converts Racenet time (e.g., '00:41:11.9970000') to milliseconds."""
    if pd.isna(time_str) or not isinstance(time_str, str):
        return 0
    try:
        # Separate the main time from the fractions of a second
        main_part, fractions = time_str.split('.')
        hours, minutes, seconds = main_part.split(':')
        
        # Take only the first 3 digits from the fractions (to get milliseconds)
        milliseconds = int(fractions[:3])
        
        # Convert everything to milliseconds
        total_time_ms = (
            (int(hours) * 3600000) +
            (int(minutes) * 60000) +
            (int(seconds) * 1000) +
            milliseconds
        )
        return total_time_ms
    except Exception as e:
        print(f"Time conversion error for value: {time_str}")
        return 0

def import_racenet_results(csv_file, rally_id, stage_number):
    conn = sqlite3.connect("wrc_liga.db")
    cursor = conn.cursor()

    # Safeguard: Ensure the rally to which we assign the results actually exists
    cursor.execute("INSERT OR IGNORE INTO seasons (id, name, is_active) VALUES (1, 'Season 1', 1)")
    cursor.execute("INSERT OR IGNORE INTO rallies (id, season_id, name) VALUES (?, 1, 'CSV Rally')", (rally_id,))

    # Load the CSV file
    df = pd.read_csv(csv_file)
    print(f"Loaded file {csv_file}. Found {len(df)} results.")

    added_records = 0

    for index, row in df.iterrows():
        # Extract data from the corresponding Racenet columns
        ea_nick = str(row['DisplayName']).strip()
        time_text = str(row['Time']).strip()
        
        # Skip empty rows
        if ea_nick == "nan" or time_text == "nan":
            continue

        # Look for the driver's ID in the database
        cursor.execute("SELECT id FROM drivers WHERE ea_nickname = ?", (ea_nick,))
        result = cursor.fetchone()

        if result is None:
            # MAGIC: Automatically add new drivers!
            print(f"➕ New driver detected: {ea_nick}. Adding to the database...")
            # Temporarily set discord_name to be the same as ea_nickname, you can change this later
            cursor.execute("INSERT INTO drivers (discord_name, ea_nickname) VALUES (?, ?)", (ea_nick, ea_nick))
            driver_id = cursor.lastrowid
        else:
            driver_id = result[0]

        # Time conversion
        time_in_ms = racenet_time_to_ms(time_text)

        # Save the result to the database (penalties and DNF are set to 0 for now)
        cursor.execute("""
            INSERT INTO stage_results (rally_id, driver_id, stage_number, time_ms, penalty_ms, is_dnf)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rally_id, driver_id, stage_number, time_in_ms, 0, 0))
        
        added_records += 1

    conn.commit()
    conn.close()
    print(f"✅ Success! Saved {added_records} results for Stage {stage_number}.")

if __name__ == "__main__":
    # Enter the exact name of your CSV file here!
    # If it's in the same folder, just enter its name.
    file_name = "wrc2023_event_5dXis5GKWfhmvqQBV_stage_overall_leaderboard_results.csv"
    
    # Try to import as Stage 1 for Rally 1
    import_racenet_results(file_name, rally_id=1, stage_number=1)