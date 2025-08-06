import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.exceptions import FirebaseError
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Firebase Admin
db = None
firebase_app = None

def initialize_firebase():
    global db, firebase_app
    
    try:
        if not firebase_admin._apps:
            # Try environment variables first
            if all(os.getenv(var) for var in [
                'FIREBASE_PRIVATE_KEY', 
                'FIREBASE_PROJECT_ID',
                'FIREBASE_PRIVATE_KEY_ID',
                'FIREBASE_CLIENT_EMAIL'
            ]):
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
                })
                firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized using environment variables")
            # Fallback to service account file
            elif os.path.exists('serviceAccountKey.json'):
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized using service account file")
            else:
                logger.error("Firebase initialization failed - no credentials provided")
                return False
        
        db = firestore.client()
        return True
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        db = None
        return False

# Initialize on import
initialize_firebase()

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