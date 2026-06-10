from flask import Flask
from app.models import db
from app.routes import main_bp
import os

app = Flask(__name__)

# Keep your exact production database URL environment setup here
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "Test-dev-key")

# Bind the database engine to this specific application instance
db.init_app(app)

with app.app_context():
    db.create_all()

# Register the routes blueprint
app.register_blueprint(main_bp)

if __name__ == '__main__':
    # Cloud Run dynamic port binding
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)