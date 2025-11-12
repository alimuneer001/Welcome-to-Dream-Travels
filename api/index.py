import os
import sys

# Set database path to /tmp for Vercel (writable location)
os.environ['DB_PATH'] = '/tmp/travel.db'

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import after path is set
from app import app, init_db, add_sample_destinations, add_admin_user

# Initialize database on first load (will recreate on each cold start)
try:
    # Always initialize to ensure tables exist
    init_db()
    # Only add sample data if database is empty
    import sqlite3
    conn = sqlite3.connect('/tmp/travel.db')
    count = conn.execute('SELECT COUNT(*) FROM destination').fetchone()[0]
    conn.close()
    if count == 0:
        add_sample_destinations()
        add_admin_user()
except Exception as e:
    # Log error but don't fail - database might already exist
    print(f"Database initialization note: {e}")

# Export the Flask app for Vercel
# Vercel expects 'handler' or the app itself
handler = app

