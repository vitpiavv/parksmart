from flask import Blueprint, jsonify, request, session
from app.models import db, User, ParkingSpot, Booking

# Create a blueprint named 'main'
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    return "Welcome to ParkSmart! Pipeline is fully functional."

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
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Look up the user in the database
    user = User.query.filter_by(username=username).first()

    # Verify user exists and check their hashed password
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    # 💡 Store user tracking data inside Flask's secure session cookie
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    return jsonify({
        "message": f"Welcome back, {user.username}!",
        "user_id": user.id,
        "role": user.role
    }), 200