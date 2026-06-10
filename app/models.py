from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # 💡 RESTORED: Required by routes.py
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='driver', nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(20), unique=True, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False) # Open by default
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Relationship to allow booking.spot.location.name to work cleanly in dashboard
    location = db.relationship('Location', backref='spots')

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(20), nullable=False)
    
    # Relationship to allow booking.spot.spot_number to resolve in dashboard
    spot = db.relationship('ParkingSpot', backref='bookings')