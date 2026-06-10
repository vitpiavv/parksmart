from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from app.models import db, User, ParkingSpot, Location

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
    db.create_all()
    
    # 1. Seed Locations first if they don't exist
    if Location.query.count() == 0:
        downtown = Location(name="Seattle Downtown Lot", address="2764 1st Ave S, Seattle, WA 98134")
        east_lot = Location(name="East Tacoma Lot", address="2617 E L St, Tacoma, WA 98421")
        db.session.add_all([downtown, east_lot])
        db.session.commit() # Commit to generate IDs
        
    # 2. Seed Parking Spots with different pricing based on location
    if ParkingSpot.query.count() == 0:
        downtown_id = Location.query.filter_by(name="Seattle Downtown Lot").first().id
        east_lot_id = Location.query.filter_by(name="East Tacoma Lot").first().id

        sample_spots = [
            # Premium Downtown Spots
            ParkingSpot(spot_number="DT-101", is_available=True, price_per_hour=7.50, location_id=downtown_id),
            ParkingSpot(spot_number="DT-102", is_available=False, price_per_hour=7.50, location_id=downtown_id),
            
            # Economy East Lot Spots
            ParkingSpot(spot_number="E-201", is_available=True, price_per_hour=4.00, location_id=east_lot_id),
            ParkingSpot(spot_number="E-202", is_available=True, price_per_hour=4.00, location_id=east_lot_id)
        ]
        db.session.bulk_save_objects(sample_spots)
        db.session.commit()
        return "Database successfully seeded with locations and multi-priced spots!"
        
    return "Data already exists."

@main_bp.route('/clear-db')
def clear_db():
    try:
        # Drops all tables defined in your models tracking
        db.drop_all()
        return "Database tables successfully dropped! Your Cloud SQL instance is now a clean slate. Time to push your updated models."
    except Exception as e:
        return f"An error occurred while clearing the database: {str(e)}", 500