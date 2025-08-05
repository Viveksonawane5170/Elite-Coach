import google.generativeai as genai
import os
from dotenv import load_dotenv
from services.firebase_service import get_user_profile

load_dotenv()

GEMINI_AVAILABLE = False
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

def generate_chat_response(question, user_id):
    if not GEMINI_AVAILABLE:
        return generate_fallback_chat_response(question)
    
    try:
        # Get user profile for context
        user_profile = get_user_profile(user_id)
        sport = user_profile.get('sport', 'general') if user_profile else 'general'
        level = user_profile.get('level', 'intermediate') if user_profile else 'intermediate'
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert sports coach assistant specializing in {sport} for {level} level athletes.
        The user has asked: "{question}"
        
        Provide a detailed, professional response that:
        1. Directly answers the question with technical accuracy
        2. Includes sport-specific advice when applicable
        3. Provides actionable recommendations
        4. Considers the athlete's level ({level})
        5. Is clear and concise (under 300 words)
        
        If the question is not sports-related, politely redirect to sports topics.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Chat generation failed: {e}")
        return generate_fallback_chat_response(question)

def generate_fallback_chat_response(question):
    return f"I'm sorry, I can't generate a response right now. Please try again later. (You asked: {question})"