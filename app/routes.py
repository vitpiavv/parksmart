from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, flash
from app.models import db, User, ParkingSpot, Booking

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def welcome():
    # Renders the modern landing template
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
        
    # Handle the submission from an HTML form
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
    if request.method == 'GET':
        return render_template('login.html')
        
    # Handle the login submission from an HTML form
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return "Invalid credentials", 401

    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    return redirect(url_for('main.welcome'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
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

    # CHANGED: Redirect straight to the dashboard instead of welcome page
    return redirect(url_for('main.dashboard'))


#  Protected Dashboard Route
@main_bp.route('/dashboard')
def dashboard():
    # Force redirect to login if an anonymous user tries to access the dashboard directly
    if not session.get('user_id'):
        return redirect(url_for('main.login'))
        
    return render_template('dashboard.html')


#  Logout Route
@main_bp.route('/logout')
def logout():
    # Clear the session cookie completely
    session.clear()
    return redirect(url_for('main.welcome'))