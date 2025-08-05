from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name
    
    @staticmethod
    def get(user_id):
        from services.firebase_service import db
        try:
            user_data = db.collection('users').document(user_id).get()
            if user_data.exists:
                return User(
                    id=user_id,
                    email=user_data.get('email'),
                    name=user_data.get('name')
                )
            return None
        except:
            return None