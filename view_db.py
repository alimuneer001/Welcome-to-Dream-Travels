import sqlite3

def view_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('travel.db')
        cursor = conn.cursor()
        
        print("\n=== DATABASE CONTENT ===\n")
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Display tables
        for table in tables:
            table_name = table[0]
            print(f"\n** Table: {table_name} **")
            
            # Get all rows
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Print column names
            print(', '.join(columns))
            print('-' * 50)
            
            # Print each row
            for row in rows:
                print(row)
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    view_database()
    print("\nPress Enter to exit...")
    input() 