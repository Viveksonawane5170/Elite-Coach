from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from firebase_admin import auth, firestore
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure CSRF protection
csrf = CSRFProtect(app)

# Configure Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Import blueprints after app creation to avoid circular imports
from auth.routes import auth_bp
from chatbot.routes import chat_bp

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(chat_bp, url_prefix='/chat')

# Import services after app creation
from services.firebase_service import db
from services.palm_service import generate_coaching_prompt

@login_manager.user_loader
def load_user(user_id):
    from auth.utils import User
    return User.get(user_id)

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
                logger.info(f"Profile saved with ID: {profile_id}")
            except Exception as e:
                profile_id = 'local'
                logger.error(f"Error saving profile: {str(e)}")
                flash('Note: Coaching not being saved to database', 'warning')
            
            # Generate prompt
            prompt = generate_coaching_prompt(user_profile)
            logger.info("Coaching prompt generated successfully")
            
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
            logger.error(f"Error generating prompt: {str(e)}")
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
            logger.info(f"Feedback saved for profile: {profile_id}")
            flash('Thank you for your feedback!', 'success')
        else:
            logger.info("Feedback recorded locally")
            flash('Feedback recorded locally', 'info')
            
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        flash(f'Error saving feedback: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Get user's previous plans
    try:
        plans = get_user_profile(current_user.id)
        logger.info(f"Retrieved {len(plans)} plans for dashboard")
    except Exception as e:
        plans = []
        logger.error(f"Error loading plans: {str(e)}")
        flash('Could not load your previous plans', 'warning')
    
    return render_template('dashboard.html', plans=plans)

def save_user_profile(profile_data):
    if db is None:
        logger.warning("Firestore not initialized - saving profile locally")
        return type('obj', (object,), {'id': 'local'})
    
    try:
        doc_ref = db.collection('user_profiles').document()
        profile_data['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(profile_data)
        logger.info(f"User profile saved: {doc_ref.id}")
        return doc_ref
    except Exception as e:
        logger.error(f"Error saving user profile: {str(e)}")
        return type('obj', (object,), {'id': 'local'})

def save_prompt_feedback(profile_id, feedback_value):
    if db is None:
        logger.warning("Firestore not initialized - feedback not saved")
        return False
    
    try:
        db.collection('user_profiles').document(profile_id).update({
            'feedback': feedback_value,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Feedback saved for profile: {profile_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        return False

def get_user_profile(user_id):
    if db is None:
        logger.warning("Firestore not initialized - returning empty profile list")
        return []
    
    try:
        docs = db.collection('user_profiles').where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        profiles = [doc.to_dict() for doc in docs]
        logger.info(f"Retrieved {len(profiles)} profiles for user: {user_id}")
        return profiles
    except Exception as e:
        logger.error(f"Error getting user profiles: {str(e)}")
        return []

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False') == 'True')