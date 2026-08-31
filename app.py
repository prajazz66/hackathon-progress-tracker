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
    
def _auto_migrate_db(db):
    """Executes safe ALTER TABLE statements to add missing columns to existing PostgreSQL or SQLite databases."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS is_idea_submission BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS header_note VARCHAR(255);",
        "ALTER TABLE participated_events ADD COLUMN IF NOT EXISTS is_idea_submission BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE participated_events ADD COLUMN IF NOT EXISTS header_note VARCHAR(255);"
    ]
    for statement in migrations:
        try:
            db.session.execute(text(statement))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                base_stmt = statement.replace(" IF NOT EXISTS", "")
                db.session.execute(text(base_stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()

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
            _auto_migrate_db(db)
            logger.info("Database connection, tables, and column migrations checked successfully.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            
    return app

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
