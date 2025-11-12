import os
import sys

# Set database path to /tmp for Vercel (writable location)
os.environ['DB_PATH'] = '/tmp/travel.db'

# Change to project root directory to ensure relative paths work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Add parent directory to path to import app
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Flask app
try:
    from app import app, init_db, add_sample_destinations, add_admin_user
except Exception as import_error:
    print(f"Failed to import app: {import_error}")
    import traceback
    traceback.print_exc()
    raise

# Initialize database on module load (Vercel caches the module)
try:
    init_db()
    # Check if we need to add sample data
    import sqlite3
    try:
        conn = sqlite3.connect('/tmp/travel.db')
        count = conn.execute('SELECT COUNT(*) FROM destination').fetchone()[0]
        conn.close()
        if count == 0:
            add_sample_destinations()
            add_admin_user()
    except Exception as db_error:
        print(f"Database check error: {db_error}")
        import traceback
        traceback.print_exc()
except Exception as init_error:
    print(f"Database initialization error: {init_error}")
    import traceback
    traceback.print_exc()
    # Continue anyway - database might be created on first request

# Export the Flask app for Vercel
# Vercel Python runtime automatically detects the 'app' variable
# This is the standard way to deploy Flask on Vercel

