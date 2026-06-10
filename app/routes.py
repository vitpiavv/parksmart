from flask import Blueprint, jsonify, request
from app.models import db, User, ParkingSpot, Booking

# Create a blueprint named 'main'
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    return "Welcome to ParkSmart! Pipeline is modular and fully secure."

@main_bp.route('/register', methods=['POST'])
def register():
    # Placeholder for registration inner logic
    return jsonify({"message": "Registration endpoint ready"}), 200

@main_bp.route('/login', methods=['POST'])
def login():
    # Placeholder for authentication inner logic
    return jsonify({"message": "Login endpoint ready"}), 200