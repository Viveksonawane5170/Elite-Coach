from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
import os
from datetime import datetime

# Import blueprints
from auth.routes import auth_bp
from chatbot.routes import chat_bp

# Import services
from services.palm_service import generate_coaching_prompt
from services.firebase_service import save_user_profile, save_prompt_feedback, get_user_profile

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(chat_bp, url_prefix='/chat')

@login_manager.user_loader
def load_user(user_id):
    from auth.utils import User
    return User.get(user_id)

# Update the index route
@app.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            if not all([request.form.get('sport'), request.form.get('level')]):
                flash('Please fill all required fields', 'error')
                return redirect(url_for('index'))
            
            # Create user profile
            user_profile = {
                'sport': request.form.get('sport'),
                'level': request.form.get('level'),
                'goals': request.form.getlist('goals'),
                'preferences': {
                    'motivational_style': request.form.get('motivational_style', 'encouraging'),
                    'length': request.form.get('length', 'medium')
                },
                'created_at': datetime.now().isoformat(),
                'user_id': current_user.id
            }
            
            # Save profile
            try:
                profile_ref = save_user_profile(user_profile)
                profile_id = profile_ref.id if hasattr(profile_ref, 'id') else 'local'
            except Exception as e:
                profile_id = 'local'
                flash('Note: Coaching not being saved to database', 'warning')
            
            # Generate prompt
            prompt = generate_coaching_prompt(user_profile)
            
            return render_template('results.html',
                       prompt=prompt,
                       profile_id=profile_id,
                       sport_name=user_profile['sport'].replace('_', ' ').title(),
                       level=user_profile['level'],
                       goals=user_profile['goals'],
                       plan_duration=request.form.get('plan_duration', '8'),
                       training_hours=request.form.get('training_hours', '0'),
                       rest_days=request.form.get('rest_days', '1'))
        
        except Exception as e:
            flash(f'Error generating prompt: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return render_template('index.html',
                         sports={},  # Will be handled in template
                         goals=[])   # Will be handled in template

@app.route('/feedback', methods=['POST'])
def feedback():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    try:
        profile_id = request.form.get('profile_id')
        feedback_value = request.form.get('feedback')
        
        if profile_id and profile_id != 'local':
            save_prompt_feedback(profile_id, feedback_value)
            flash('Thank you for your feedback!', 'success')
        else:
            flash('Feedback recorded locally', 'info')
            
    except Exception as e:
        flash(f'Error saving feedback: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get user's previous plans
    try:
        plans = get_user_profile(current_user.id)
    except Exception as e:
        plans = []
        flash('Could not load your previous plans', 'warning')
    
    return render_template('dashboard.html', plans=plans)

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')