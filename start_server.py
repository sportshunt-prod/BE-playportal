#!/usr/bin/env python3
"""
Cross-platform production server for SportsHunt
Supports both Windows (Waitress) and Unix (Gunicorn)
"""

import os
import sys
import platform
from pathlib import Path

def ensure_logs():
    """Ensure logs directory exists"""
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"✅ Logs directory ensured at: {logs_dir}")
    return logs_dir

def install_server_package():
    """Install the appropriate WSGI server"""
    import subprocess
    
    if platform.system() == 'Windows':
        package = 'waitress'
    else:
        package = 'gunicorn'
    
    print(f"📦 Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print(f"✅ {package} installed successfully")

def run_windows_server():
    """Run server using Waitress (Windows compatible)"""
    try:
        from waitress import serve
        from sportshunt.wsgi import application
        
        print("🚀 Starting SportsHunt with Waitress...")
        print("🌐 Server running at http://127.0.0.1:8000")
        print("⏹️  Press Ctrl+C to stop the server")
        
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
        print("❌ Waitress not installed.")
        install_server_package()
        print("🔄 Please run this script again.")

def run_unix_server():
    """Run server using Gunicorn (Unix systems)"""
    try:
        import gunicorn.app.wsgiapp as wsgi
        
        print("🚀 Starting SportsHunt with Gunicorn...")
        print("🌐 Server running at http://127.0.0.1:8000")
        print("⏹️  Press Ctrl+C to stop the server")
        
        # Gunicorn command line args
        sys.argv = [
            'gunicorn',
            '--bind', '127.0.0.1:8000',
            '--workers', '2',
            '--timeout', '30',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info',
            'sportshunt.wsgi:application'
        ]
        
        wsgi.run()
        
    except ImportError:
        print("❌ Gunicorn not installed.")
        install_server_package()
        print("🔄 Please run this script again.")

def main():
    """Main entry point"""
    print("🏆 SportsHunt Production Server")
    print("=" * 40)
    
    # Set up environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportshunt.conf.prod')
    
    # Ensure logs directory
    ensure_logs()
    
    try:
        # Choose server based on platform
        if platform.system() == 'Windows':
            run_windows_server()
        else:
            run_unix_server()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
