from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from app.models import db, User, ParkingSpot

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'GET':
        return render_template('register.html')
        
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        return "Missing fields", 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return "User already exists", 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('main.login'))



@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'GET':
        return render_template('login.html')
        
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return "Invalid credentials", 401

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('main.login'))

    spots = ParkingSpot.query.all()    
    return render_template('dashboard.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.welcome'))

@main_bp.route('/seed-spots')
def seed_spots():
    # Only seed if the table is currently empty to avoid duplicates
    if ParkingSpot.query.count() == 0:
        sample_spots = [
            ParkingSpot(spot_number="A-101", level="G1", is_available=True, price_per_hour=5.00),
            ParkingSpot(spot_number="A-102", level="G1", is_available=False, price_per_hour=5.00),
            ParkingSpot(spot_number="B-201", level="G2", is_available=True, price_per_hour=7.50),
            ParkingSpot(spot_number="B-202", level="G2", is_available=True, price_per_hour=7.50)
        ]
        db.session.bulk_save_objects(sample_spots)
        db.session.commit()
        return "Database successfully seeded with 4 parking spots! Go back to /dashboard."
    
    return "Spots already exist in the database. Go back to /dashboard."