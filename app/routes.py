from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from app.models import db, User, ParkingSpot, Location, Booking

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

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.welcome'))

@main_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('main.login'))
        
    # 1. Get all available locations for our tab switcher
    locations = Location.query.all()
    if not locations:
        return render_template('dashboard.html', locations=[], selected_location=None, spots=[], active_bookings=[])

    # 2. Determine which location is currently selected (default to the first one)
    selected_location_name = request.args.get('location', locations[0].name)
    selected_location = Location.query.filter_by(name=selected_location_name).first()

    # 3. Get spots only for the selected location
    spots = ParkingSpot.query.filter_by(location_id=selected_location.id).order_by(ParkingSpot.spot_number).all() if selected_location else []

    # 4. Fetch any active bookings for the current user to display at the top
    active_bookings = Booking.query.filter_by(user_id=session['user_id'], status='active').all()

    return render_template(
        'dashboard.html', 
        locations=locations, 
        selected_location=selected_location, 
        spots=spots,
        active_bookings=active_bookings
    )

@main_bp.route('/seed-spots')
def seed_spots():
    from app import db
    
    db.create_all()
    
    # 1. Seed Locations
    if Location.query.count() == 0:
        seattle = Location(
            name="Seattle Downtown Lot", 
            address="2764 1st Ave S, Seattle, WA 98134"
        )
        tacoma = Location(
            name="East Tacoma Lot", 
            address="2617 E L St, Tacoma, WA 98421"
        )
        db.session.add_all([seattle, tacoma])
        db.session.commit()
        
    # 2. Seed an expanded collection of 10 Parking Spots per lot
    if ParkingSpot.query.count() == 0:
        seattle_id = Location.query.filter_by(name="Seattle Downtown Lot").first().id
        tacoma_id = Location.query.filter_by(name="East Tacoma Lot").first().id

        sample_spots = []

        # Generate 10 Premium Seattle Spots (SEA-01 through SEA-10) at $7.50/hr
        for i in range(1, 11):
            spot_num = f"SEA-{i:02d}"
            is_avail = True 
            sample_spots.append(
                ParkingSpot(
                    spot_number=spot_num, 
                    is_available=is_avail, 
                    price_per_hour=7.50, 
                    location_id=seattle_id
                )
            )

        # Generate 10 Economy Tacoma Spots (TAC-01 through TAC-10) at $4.00/hr
        for i in range(1, 11):
            spot_num = f"TAC-{i:02d}"
            is_avail = True  # 💡 FIX: Removed the trailing comma so this remains a boolean
            sample_spots.append(
                ParkingSpot(
                    spot_number=spot_num, 
                    is_available=is_avail, 
                    price_per_hour=4.00, 
                    location_id=tacoma_id
                )
            )

        db.session.bulk_save_objects(sample_spots)
        db.session.commit()
        return "Database successfully seeded with 20 premium and economy spots across Seattle & Tacoma! Go back to /dashboard."
    
    return "Data already exists."

@main_bp.route('/clear-db')
def clear_db():
    try:
        # Drops all tables defined in your models tracking
        db.drop_all()
        return "Database tables successfully dropped! Your Cloud SQL instance is now a clean slate. Time to push your updated models."
    except Exception as e:
        return f"An error occurred while clearing the database: {str(e)}", 500

@main_bp.route('/reserve/<int:spot_id>', methods=['POST'])
def reserve_spot(spot_id):
    if not session.get('user_id'):
        return redirect(url_for('main.login'))

    # Fetch the spot and ensure it's actually available
    spot = ParkingSpot.query.get_or_404(spot_id)
    if not spot.is_available:
        # If someone else beat them to it, bounce back with a note (or silent refresh)
        return redirect(url_for('main.dashboard', location=spot.location.name))

    # Transaction: 1. Mark spot as occupied
    spot.is_available = False

    # Transaction: 2. Create the booking receipt record
    new_booking = Booking(
        user_id=session['user_id'],
        spot_id=spot.id,
        status='active'
    )
    
    db.session.add(new_booking)
    db.session.commit()

    # Redirect right back to the active location tab view
    return redirect(url_for('main.dashboard', location=spot.location.name))

@main_bp.route('/admin/dashboard')
def admin_dashboard():
    # Security Guardrails: Must be logged in AND an admin
    if not session.get('user_id'):
        return redirect(url_for('main.login'))
    if session.get('role') != 'admin':
        return "Access Denied: Administrative privileges required.", 403

    # 1. Fetch all locations and spots for overview panels
    locations = Location.query.all()
    all_spots = ParkingSpot.query.all()
    
    # 2. Calculate quick high-level business metrics
    total_spots = len(all_spots)
    occupied_spots = len([s for s in all_spots if not s.is_available])
    available_spots = total_spots - occupied_spots
    
    # Calculate occupancy rate percentage safely
    occupancy_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0

    # 3. Get all active transactions to show who is parked where
    active_bookings = Booking.query.filter_by(status='active').all()

    return render_template(
        'admin_dashboard.html',
        locations=locations,
        all_spots=all_spots,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        available_spots=available_spots,
        occupancy_rate=round(occupancy_rate, 1),
        active_bookings=active_bookings
    )

@main_bp.route('/admin/update-price/<int:spot_id>', methods=['POST'])
def update_price(spot_id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
        
    spot = ParkingSpot.query.get_or_404(spot_id)
    new_price = request.form.get('price', type=float)
    
    if new_price and new_price > 0:
        spot.price_per_hour = new_price
        db.session.commit()
        
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/cancel-booking/<int:booking_id>', methods=['POST'])
def admin_cancel_booking(booking_id):
    # Security Guardrail: Only active admins can force-cancel sessions
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    # 1. Fetch the targeted booking receipt
    booking = Booking.query.get_or_404(booking_id)
    
    # 2. Safety Check: Only cancel if it's currently active
    if booking.status == 'active':
        booking.status = 'cancelled'
        
        # 3. Pull the linked physical parking spot and make it available again
        if booking.spot:
            booking.spot.is_available = True
            
        db.session.commit()
        
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/promote-admin')
def promote_admin():
    from app import db
    
    # Locate the target user profile
    user = User.query.filter_by(username='admin').first()
    if not user:
        return "User 'admin' not found. Please register an account with the username 'admin' first.", 404
        
    # Elevate access rights
    user.role = 'admin'
    db.session.commit()
    
    return "Success! The user 'admin' has been promoted to admin privileges."