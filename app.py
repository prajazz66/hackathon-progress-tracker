from flask import Flask
from config import Config
from extensions import db
from routes.auth_routes import auth_bp
from routes.hackathon_routes import hackathon_bp
from routes.file_routes import file_bp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(hackathon_bp)
    app.register_blueprint(file_bp)
    
    # Initialize database tables cleanly with error catching
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database connection and tables checked successfully.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            
    return app

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
