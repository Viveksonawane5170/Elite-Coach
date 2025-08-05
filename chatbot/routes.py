from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .service import generate_chat_response

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_home():
    return render_template('chat.html')

@chat_bp.route('/ask', methods=['POST'])
@login_required
def ask_question():
    question = request.form.get('question')
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        response = generate_chat_response(question, current_user.id)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500