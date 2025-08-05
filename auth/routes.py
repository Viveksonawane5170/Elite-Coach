from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .utils import User
from services.firebase_service import db, auth as firebase_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        try:
            # Verify user with Firebase
            user = firebase_auth.sign_in_with_email_and_password(email, password)
            user_info = firebase_auth.get_account_info(user['idToken'])
            
            # Create Flask-Login user
            flask_user = User(
                id=user_info['users'][0]['localId'],
                email=email,
                name=user_info['users'][0].get('displayName', '')
            )
            
            login_user(flask_user, remember=remember)
            return redirect(url_for('index'))
        except Exception as e:
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
        
        try:
            # Create user in Firebase
            user = firebase_auth.create_user_with_email_and_password(email, password)
            
            # Update user profile with name
            firebase_auth.update_profile(user['idToken'], display_name=name)
            
            # Create Flask-Login user
            flask_user = User(
                id=user['localId'],
                email=email,
                name=name
            )
            
            login_user(flask_user)
            return redirect(url_for('index'))
        except Exception as e:
            flash('Error creating account: ' + str(e), 'error')
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))