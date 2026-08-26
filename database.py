import sqlite3
import os

os.makedirs("data", exist_ok=True)
DB_PATH = "data/travel_engine.db"

def initialize_project_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            latitude REAL,
            longitude REAL,
            history_summary TEXT,
            realness_status TEXT,
            terrain_challenge TEXT,
            driving_route_json TEXT,
            trekking_route_json TEXT,
            cycling_route_json TEXT
        )
    ''')
    connection.commit()
    connection.close()

def save_and_verify_test_data():
    """Injects a test place to prove data writes directly to our local file."""
    # 1. Connect directly to our file path target
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # 2. Insert a dummy tourist location data block
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO places (name, latitude, longitude, history_summary, realness_status)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Test Beach Paradise", 15.2993, 73.8111, "A beautiful pilot destination testing our zero-RAM file database framework.", "Underrated Gem"))
        connection.commit()
        print("💾 [Success] Data written directly into data/travel_engine.db file!")
    except Exception as e:
        print(f"❌ Write Error: {e}")

    # 3. Read it back instantly to confirm it is physically saved on the disk
    cursor.execute("SELECT * FROM places")
    all_saved_rows = cursor.fetchall()
    connection.close()
    
    print("\n🔍 --- Live Database File Content Reading ---")
    for row in all_saved_rows:
        print(f"📍 ID: {row[0]} | Name: {row[1]} | Status: {row[5]}")

if __name__ == "__main__":
    initialize_project_database()
    save_and_verify_test_data()
