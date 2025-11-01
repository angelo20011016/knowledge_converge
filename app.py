import asyncio
import threading
import uuid
from pathlib import Path
import sys
from functools import wraps
from flask_cors import CORS
from flask import Flask, request, jsonify, url_for, redirect
import os
import re
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, date
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path to import main
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the refactored main functions
from main import run_analysis_for_url

# --- Job Management ---
JOBS = {}

app = Flask(__name__)
CORS(app)

# --- Configuration ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-super-secret-key-and-you-should-change-it')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(project_root, 'project.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_NAME'] = os.getenv('FLASK_SERVER_NAME')
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

from models import db, Template, User, IPUsage
db.init_app(app)
migrate = Migrate(app, db)

# --- OAuth Configuration ---
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)





# --- API Routes ---

@app.route('/')
def index():
    return "Video Knowledge Convergence Backend is running!"

# Decorator for JWT token verification
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['sub']).first()
            if not current_user:
                return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/start-url-summary', methods=['POST'])
@token_required
def start_url_summary(current_user):
    data = request.get_json()
    url = data.get('url')
    title = data.get('title') 
    language = data.get('language', 'en')
    template_id = data.get('template_id')
    user_additional_prompt = data.get('user_additional_prompt')

    template_content = None
    if template_id:
        template = Template.query.get(template_id)
        if template:
            template_content = template.content
        else:
            return jsonify({"error": "Template not found"}), 404

    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    # Directly call the analysis function, making it a blocking request
    try:
        result = asyncio.run(run_analysis_for_url(
            user_id=current_user.id, # Pass user_id
            url=url,
            title=title,
            language=language,
            template_content=template_content,
            user_additional_prompt=user_additional_prompt
        ))
        if result.get("status") == "success":
            return jsonify(result)
        else:
            return jsonify({"error": result.get("message", "An unknown error occurred.")}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# The get-job-result endpoint is no longer needed for this simplified flow
@app.route('/api/get-job-result/<job_id>')
def get_job_result(job_id):
    return jsonify({"status": "deprecated"}), 404

# --- User Authentication API ---

@app.route('/api/login/google')
def google_login():
    redirect_uri = url_for('google_auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/api/auth/google')
def google_auth_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.userinfo()
    sso_id = user_info['sub']
    email = user_info['email']

    user = User.query.filter_by(sso_id=sso_id).first()
    if not user:
        user = User.query.filter_by(username=email).first()
        if not user:
            user = User(username=email, sso_id=sso_id)
            db.session.add(user)
        else:
            user.sso_id = sso_id
        db.session.commit()

    jwt_token = jwt.encode({
        'sub': user.id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return redirect(f'{FRONTEND_URL}/login/success?token={jwt_token}')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"id": new_user.id, "username": new_user.username}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = jwt.encode({
        'sub': user.id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})

# --- Template Management API ---
@app.route('/api/templates', methods=['POST'])
def create_template():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')

    if not name or not content:
        return jsonify({"error": "Template name and content are required"}), 400

    # Hardcode user_id to 1 for simplicity
    template = Template(name=name, content=content, user_id=1)
    db.session.add(template)
    db.session.commit()
    return jsonify({
        "id": template.id,
        "name": template.name,
        "content": template.content,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat()
    }), 201

@app.route('/api/templates', methods=['GET'])
def get_templates():
    # Return all templates, not filtered by user
    templates = Template.query.order_by(Template.updated_at.desc()).all()
    return jsonify([{
        "id": t.id,
        "name": t.name,
        "content": t.content,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat()
    } for t in templates]), 200

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    template = Template.query.get(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    # Removed permission check
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')

    if name:
        template.name = name
    if content:
        template.content = content
    
    template.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        "id": template.id,
        "name": template.name,
        "content": template.content,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat()
    }), 200

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    template = Template.query.get(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    # Removed permission check
    db.session.delete(template)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)