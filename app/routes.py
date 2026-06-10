from flask import Blueprint, jsonify, request
from app.models import db, User, ParkingSpot, Booking

# Create a blueprint named 'main'
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    return "Welcome to ParkSmart! Pipeline is modular and fully secure."

@main_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 1. Basic validation
    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    # 2. Check if user or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    # 3. Create the new user and securely hash their password
    new_user = User(username=username, email=email)
    new_user.set_password(password) # This triggers Werkzeug password hashing under the hood!

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully!", "user_id": new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred", "details": str(e)}), 500

@main_bp.route('/login', methods=['POST'])
def login():
    # Placeholder for authentication inner logic
    return jsonify({"message": "Login endpoint ready"}), 200