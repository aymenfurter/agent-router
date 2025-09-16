from flask import Flask, send_from_directory, send_file
import os
import atexit
from backend.utils.logging_config import setup_logging
from backend.config.settings import settings
from backend.api.health_routes import health_bp
from backend.api.query_routes import query_bp
from backend.api.thread_routes import thread_bp
from backend.services.connected_agent_service import connected_agent_service

# Setup logging
setup_logging()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(query_bp)
app.register_blueprint(thread_bp)

# Path to the built UI files
DIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
)

@app.route('/')
def index():
    """Serve the main index.html file"""
    return send_file(os.path.join(DIST_DIR, 'index.html'))

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (JS, CSS, images, etc.)"""
    return send_from_directory(DIST_DIR, filename)

@app.teardown_appcontext
def cleanup_service(error):
    """Cleanup service resources on app teardown"""
    if error:
        app.logger.error(f"App context teardown due to error: {error}")

def cleanup_on_exit():
    """Cleanup function called on app shutdown"""
    app.logger.info("Cleaning up Connected Agent Service...")
    connected_agent_service.cleanup()

if __name__ == '__main__':
    # Register cleanup function
    atexit.register(cleanup_on_exit)
    
    # Check if dist directory exists
    if not os.path.exists(DIST_DIR):
        print("❌ Build files not found!")
        print("💡 Run './scripts/build_all.sh' first to build the UI")
        exit(1)
    
    print("🚀 Starting Purview Router server...")
    print(f"📁 Serving files from: {DIST_DIR}")
    print("🌐 Open http://localhost:5000 in your browser")
    print("🤖 Connected Agent Service will initialize on first request")
    
    try:
        app.run(
            host=settings.FLASK_HOST,
            port=settings.FLASK_PORT, 
            debug=settings.FLASK_DEBUG
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    finally:
        cleanup_on_exit()
