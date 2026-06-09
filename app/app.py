import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(10), unique=True, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

def create_app():
    app = Flask(__name__)
    
    # Configure Database Connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'postgresql://parkuser:parkpassword@db:5432/parksmart'
    )
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-123')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind DB extension to the app
    db.init_app(app)

    # Force database tables to create on startup
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        try:
            spots = ParkingSpot.query.all()
            return f"Welcome to ParkSmart! Successfully connected to DB. Found {len(spots)} spots."
        except Exception as e:
            return f"Database connected, but failed to query: {str(e)}", 500

    return app

# Gunicorn targets this specific variable
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)