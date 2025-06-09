# Windows-compatible WSGI server configuration
# Since Gunicorn doesn't work on Windows, we'll use Waitress instead

# Install waitress: pip install waitress

import os
from pathlib import Path

# Ensure logs directory exists before starting
def ensure_logs():
    """Ensure logs directory exists"""
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"Logs directory ensured at: {logs_dir}")
    return logs_dir

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    # Set production environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportshunt.conf.prod')
    
    # Ensure logs directory
    ensure_logs()
    
    try:
        from waitress import serve
        from sportshunt.wsgi import application
        
        print("Starting SportsHunt with Waitress...")
        print("Server running at http://127.0.0.1:8000")
        print("Press Ctrl+C to stop the server")
        
        # Serve the application
        serve(
            application,
            host='127.0.0.1',
            port=8000,
            threads=4,
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120,
            expose_tracebacks=False
        )
        
    except ImportError:
        print("Waitress not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])
        print("Please run this script again after installation.")
        
    except KeyboardInterrupt:
        print("\nServer stopped.")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
