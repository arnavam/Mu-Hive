import sqlite3

def view_database():
    try:
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            print("The 'events' table does not exist or the database is perfectly empty.")
            return

        # Fetch all rows
        cursor.execute("SELECT * FROM events")
        rows = cursor.fetchall()
        
        if not rows:
            print("The 'events' table is completely empty.")
        else:
            print(f"Total events recorded: {len(rows)}\n")
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Title: {row[1]}")
                print(f"Link: {row[2]}")
                print(f"Keyword: {row[3]}")
                print(f"Engine: {row[4]}")
                print(f"Status: {row[5]}")
                print(f"Timestamp: {row[6]}")
                print("-" * 50)
                
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    view_database()
