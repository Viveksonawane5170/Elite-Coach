from flask_login import UserMixin
import logging

logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name
    
    @staticmethod
    def get(user_id):
        from services.firebase_service import db
        try:
            user_ref = db.collection('users').document(user_id)
            user_data = user_ref.get()
            
            if user_data.exists:
                logger.info(f"User found in Firestore: {user_id}")
                return User(
                    id=user_id,
                    email=user_data.get('email'),
                    name=user_data.get('name')
                )
            logger.warning(f"User not found in Firestore: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None