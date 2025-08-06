from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError
from .utils import User
from services.firebase_service import db
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        try:
            # Verify user with Firebase Admin SDK
            user = auth.get_user_by_email(email)
            
            # Create Flask-Login user
            flask_user = User(
                id=user.uid,
                email=user.email,
                name=user.display_name or ''
            )
            
            login_user(flask_user, remember=remember)
            return redirect(url_for('index'))
        except FirebaseError as e:
            logger.error(f"Login error: {str(e)}")
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not all([email, name, password]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('auth.signup'))
        
        try:
            # Create user with Firebase Admin SDK
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Store additional user data in Firestore
            user_data = {
                'email': email,
                'name': name,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            if db:
                db.collection('users').document(user.uid).set(user_data)
                logger.info(f"User created in Firestore: {user.uid}")
            
            # Create Flask-Login user
            flask_user = User(
                id=user.uid,
                email=email,
                name=name
            )
            
            login_user(flask_user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        except FirebaseError as e:
            logger.error(f"Signup error: {str(e)}")
            if 'email already exists' in str(e).lower():
                flash('Email already in use', 'error')
            else:
                flash('Error creating account. Please try again.', 'error')
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))