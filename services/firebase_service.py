import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.auth import UserNotFoundError
import os
from dotenv import load_dotenv
import pyrebase

load_dotenv()

# Initialize Firebase Admin
db = None
firebase_auth = None

def initialize_firebase():
    global db, firebase_auth
    
    try:
        if not firebase_admin._apps:
            # Try environment variables first
            if os.getenv('FIREBASE_PRIVATE_KEY'):
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
                firebase_admin.initialize_app(cred)
            # Fallback to service account file
            elif os.path.exists('serviceAccountKey.json'):
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Initialize Pyrebase for client-side auth
        firebase_config = {
            "apiKey": os.getenv('FIREBASE_API_KEY'),
            "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
            "projectId": os.getenv('FIREBASE_PROJECT_ID'),
            "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
            "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
            "appId": os.getenv('FIREBASE_APP_ID'),
            "databaseURL": ""
        }
        
        firebase_auth = pyrebase.initialize_app(firebase_config).auth()
        return True
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        db = None
        firebase_auth = None
        return False

# Initialize on import
initialize_firebase()

def save_user_profile(profile_data):
    if db is None:
        return type('obj', (object,), {'id': 'local'})
    
    try:
        doc_ref = db.collection('user_profiles').document()
        profile_data['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(profile_data)
        return doc_ref
    except Exception:
        return type('obj', (object,), {'id': 'local'})

def save_prompt_feedback(profile_id, feedback_value):
    if db is None:
        return False
    
    try:
        db.collection('user_profiles').document(profile_id).update({
            'feedback': feedback_value,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception:
        return False

def get_user_profile(user_id):
    if db is None:
        return []
    
    try:
        docs = db.collection('user_profiles').where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []