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

# Import Flask app at TOP LEVEL so Vercel static analysis can find it
# Vercel requires 'app', 'application', or 'handler' as a module-level variable
from app import app, init_db, add_sample_destinations, add_admin_user  # noqa: E402

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

# 'app' is already at module level from the import above.
# Vercel detects it here as the WSGI entry point.
