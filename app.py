import asyncio
import threading
import uuid
import hmac
from pathlib import Path
import sys
from flask_cors import CORS
from flask import Flask, request, jsonify, session, redirect, url_for
import os
import re # Keep re for URL validation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta # Import datetime for Template model
from authlib.integrations.flask_client import OAuth
from flask_sse import sse

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# Add the project root to the Python path to import main
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the refactored main functions
from main import run_analysis_for_url, get_video_info_from_url

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-for-dev") # For session management
app.config['SESSION_COOKIE_NAME'] = 'video_knowledge_session'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
# --- SSE Configuration (REMOVED) ---

# --- OAuth (Google SSO) Configuration ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    # Use the OpenID Connect discovery document to automatically configure all endpoints.
    # This is the modern and recommended approach.
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# --- CORS Configuration ---
# This is crucial for the frontend (running on localhost:3000) to be able
# to send requests and receive session cookies from the backend (running on localhost:5000).
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://noledge.happywecan.com"])

# --- Startup Check for Environment Variables ---
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET environment variables. Please set them in your .env file.")

# --- Database Configuration ---
data_dir = project_root / 'data'
data_dir.mkdir(exist_ok=True) # Ensure the data directory exists
db_path = data_dir / 'project.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from models import db, Template, Job, User, Feedback
db.init_app(app)

migrate = Migrate(app, db)

# --- Rate Limiter Configuration ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# --- Admin Panel Configuration ---
class AdminModelView(ModelView):
    def is_accessible(self):
        # Check if a user is logged in via session
        user_id = session.get('user_id')
        if not user_id:
            return False

        # Get the required admin Google ID from environment variables
        admin_google_id = os.environ.get('ADMIN_GOOGLE_ID')
        if not admin_google_id:
            print("Warning: ADMIN_GOOGLE_ID is not set. Admin panel is inaccessible.")
            return False

        # Fetch the user from the database
        user = User.query.get(user_id)
        if not user:
            return False

        # Check if the logged-in user's Google ID matches the admin's Google ID
        print(f"[Admin Check] DB Google ID: '{user.google_id}' (Type: {type(user.google_id)})")
        print(f"[Admin Check] ENV Google ID: '{admin_google_id}' (Type: {type(admin_google_id)})")
        return user.google_id == admin_google_id

    def inaccessible_callback(self, name, **kwargs):
        # If user is not an admin, redirect them to the Google login page.
        return redirect(url_for('login'))

class UserAdminView(AdminModelView):
    # Columns to display in the list view
    column_list = ['id', 'name', 'email', 'created_at', 'usage_limit']
    # Exclude certain columns from the edit form to avoid a bug in form generation
    form_excluded_columns = ['google_id', 'profile_pic', 'created_at', 'jobs', 'templates']

admin = Admin(app, name='Video Knowledge Admin', template_mode='bootstrap4', url='/admin')
admin.add_view(UserAdminView(User, db.session))
admin.add_view(AdminModelView(Job, db.session))
admin.add_view(AdminModelView(Feedback, db.session))

# --- Helper function for the analysis thread ---
def run_analysis_in_background(job_id, analysis_func, url, title, language, template_content, user_additional_prompt):
    """
    Wrapper to run an analysis function, update the JOBS dict, and handle errors.
    (SSE progress updates have been disabled and replaced with console logs).
    """
    with app.app_context():
        def progress_callback(percentage, message):
            """Prints progress messages to the console for this job."""
            print(f"[Progress-{job_id}] {percentage}%: {message}")

        try:
            job = Job.query.get(job_id)
            if not job:
                print(f"Job {job_id} not found in database.")
                return
            job.status = 'running'
            db.session.commit()
            progress_callback(5, "Job started, analysis is running...")

            # Pass the callback to the analysis function
            result = asyncio.run(analysis_func(
                url=url,
                title=title,
                language=language,
                job_id=job_id,
                template_content=template_content,
                user_additional_prompt=user_additional_prompt,
                progress_callback=progress_callback
            ))

            if result.get("status") == "success":
                job.status = 'success'
                job.result = result.get("result")
                progress_callback(100, "Job completed successfully.")
            else:
                job.status = 'error'
                job.error_message = result.get("message", "An unknown error occurred.")
                progress_callback(100, f"Job failed: {job.error_message}")
            
            db.session.commit()
            print(f"Thread finished for job_id: {job_id}, status: {job.status}")

        except Exception as e:
            import traceback
            print(f"An unhandled exception occurred in thread for job {job_id}: {e}")
            traceback.print_exc()
            job.status = 'error'
            job.error_message = str(e)
            db.session.commit()
            progress_callback(100, f"A critical error occurred: {e}")


@app.route('/')
def index():
    return "Video Knowledge Convergence Backend is running!"

@app.route('/api/start-url-summary', methods=['POST'])
def start_url_summary():
    """
    Starts the analysis for a single YouTube URL.
    Returns a job_id to the client for polling the result.
    """
    data = request.get_json()
    url = data.get('url')
    title = data.get('title') 
    language = data.get('language', 'en')
    template_id = data.get('template_id') # Get template_id
    user_additional_prompt = data.get('user_additional_prompt') # Get user_additional_prompt

    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    # URL validation
    url_pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+')
    if not url_pattern.match(url):
        return jsonify({"error": "Invalid YouTube URL format."}), 400

    # --- Quota Check ---
    # Moved after URL validation to avoid charging for invalid inputs
    user_id = session.get('user_id')
    today = datetime.utcnow().date()
    
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404
        user_limit = user.usage_limit
        usage_count = Job.query.filter(Job.user_id == user_id, Job.status != 'error', db.func.date(Job.created_at) == today).count()
        if usage_count >= user_limit:
            return jsonify({"error": f"Daily usage limit of {user_limit} reached for logged-in users."}), 429
    else:
        # Anonymous user: 1 time per day per IP
        ip_address = request.remote_addr
        usage_count = Job.query.filter(Job.ip_address == ip_address, Job.status != 'error', db.func.date(Job.created_at) == today).count()
        if usage_count >= 1:
            return jsonify({"error": "Daily usage limit of 1 reached for anonymous users."}), 429

    # --- Get Template ---
    template_content = None
    if template_id:
        template = Template.query.get(template_id)
        if template:
            template_content = template.content
        else:
            return jsonify({"error": "Template not found"}), 404

    # --- Create Job in DB ---
    video_info = get_video_info_from_url(url)
    video_title = video_info.get("title") if video_info else "Unknown Video"

    job_id = str(uuid.uuid4())
    new_job = Job(
        id=job_id,
        status='starting',
        user_id=user_id,
        ip_address=request.remote_addr if not user_id else None,
        video_url=url,
        video_title=video_title
    )
    db.session.add(new_job)
    db.session.commit()
    
    # Pass arguments directly to the background function
    thread = threading.Thread(
        target=run_analysis_in_background,
        args=(
            job_id, run_analysis_for_url,
            url, title, language, template_content, user_additional_prompt
        )
    )
    thread.start()
    
    # Immediately return the job_id
    return jsonify({"job_id": job_id}), 202

# The /api/start-topic-search endpoint has been removed as its implementation was incomplete in the source.

@app.route('/api/get-job-result/<job_id>')
def get_job_result(job_id):
    """
    Pollable endpoint for the frontend to get the status and result of a job.
    """
    job = Job.query.get(job_id)
    
    if not job:
        return jsonify({"status": "not_found"}), 404
    
    if job.status == 'success':
        result_data = job.result or {}
        formatted_result = {
            "title": result_data.get("title"),
            "url": result_data.get("url"),
            "summary": result_data.get("summary"),
            "full_transcript": result_data.get("full_transcript")
        }
        return jsonify({"status": "success", "data": formatted_result})
    else:
        return jsonify({"status": job.status, "message": job.error_message})

# --- Template Management API ---
@app.route('/api/templates', methods=['POST'])
def create_template():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User must be logged in to create templates"}), 401

    if not name or not content:
        return jsonify({"error": "Template name and content are required"}), 400

    # Add user_additional_prompt to the content
    template = Template(name=name, content=content, user_id=user_id)
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
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([]), 200 # Return empty list if not logged in

    templates = Template.query.filter_by(user_id=user_id).order_by(Template.updated_at.desc()).all()
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
    
    user_id = session.get('user_id')
    if template.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    name = data.get('name')
    content = data.get('content')

    if name:
        template.name = name
    if content:
        template.content = content
    
    template.updated_at = datetime.utcnow() # Manually update timestamp
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

    user_id = session.get('user_id')
    if template.user_id != user_id:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(template)
    db.session.commit()
    return '', 204

# --- User Session and History API ---
@app.route('/api/login')
def login():
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        raise ValueError("GOOGLE_REDIRECT_URI environment variable is not set.")
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth')
def auth():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return f"Authentication failed. Please try again. Error: {e}", 400

    user_info = token.get('userinfo')
    if not user_info:
        return "Could not retrieve user info from token.", 400

    # Use 'sub' (Subject) from the OIDC token to find the user
    user = User.query.filter_by(google_id=user_info['sub']).first()
    if not user:
        user = User(
            google_id=user_info['sub'],
            name=user_info['name'],
            email=user_info['email'],
            profile_pic=user_info.get('picture')
        )
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_pic'] = user.profile_pic

    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    return f'<script>window.location.href="{frontend_url}";</script>'

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/session')
def get_session():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if not user:
            # This should ideally not happen if user_id is in session but user is deleted
            return jsonify({"logged_in": False}), 404
        today = datetime.utcnow().date()
        usage_count = Job.query.filter(Job.user_id == user_id, db.func.date(Job.created_at) == today).count()
        quota = user.usage_limit
        return jsonify({
            "logged_in": True,
            "user": {
                "id": user_id,
                "name": session.get('user_name'),
                "picture": session.get('user_pic')
            },
            "usage": {
                "used": usage_count,
                "quota": quota
            }
        })

@app.route('/api/history')
def get_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    jobs = Job.query.filter_by(user_id=user_id).order_by(Job.created_at.desc()).all()
    
    return jsonify([{
        "job_id": job.id,
        "video_title": job.video_title,
        "video_url": job.video_url,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "summary": job.result.get('summary') if job.status == 'success' and job.result else None,
        "full_transcript": job.result.get('full_transcript') if job.status == 'success' and job.result else None
    } for job in jobs])

# --- Feedback API ---
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({"error": "Feedback content is required"}), 400

    user_id = session.get('user_id')
    feedback = Feedback(content=content, user_id=user_id)
    db.session.add(feedback)
    db.session.commit()

    return jsonify({"message": "Feedback submitted successfully"}), 201


if __name__ == '__main__':
    # IMPORTANT: use_reloader=False is critical to prevent the server from
    # restarting when background threads write output files.
    # The reloader should be disabled to prevent background threads from being
    # interrupted or restarted when they write files.
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)