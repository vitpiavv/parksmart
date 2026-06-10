import os
from flask import Flask
from app.models import db
from app.routes import main_bp

def create_app():
    app = Flask(__name__)

    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Secure Session Key
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "super-secret-dev-key-123")

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)

    return app

# Gunicorn targets this variable directly
app = create_app()