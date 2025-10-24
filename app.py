import asyncio
import threading
import uuid
from pathlib import Path
import sys
from flask_cors import CORS
from flask import Flask, request, jsonify
import os
import re # Keep re for URL validation
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime # Import datetime for Template model

# Add the project root to the Python path to import main
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the refactored main functions
from main import run_analysis, run_analysis_for_url

# --- Job Management ---
# A thread-safe dictionary to store the status and results of background jobs.
JOBS = {}

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(project_root, 'project.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from models import db, Template
db.init_app(app)

migrate = Migrate(app, db)

# --- Helper function for the analysis thread ---
def run_analysis_in_background(job_id, analysis_func, *args, **kwargs):
    """
    Wrapper to run an analysis function, update the JOBS dict, and handle errors.
    """
    print(f"Thread started for job_id: {job_id}")
    try:
        # Initialize status
        JOBS[job_id] = {"status": "running", "result": None}
        
        # Run the async analysis function
        result = asyncio.run(analysis_func(*args, **kwargs))
        
        # Store the final result
        if result.get("status") == "success":
            JOBS[job_id] = {"status": "success", "result": result.get("result")}
        else:
            JOBS[job_id] = {"status": "error", "message": result.get("message", "An unknown error occurred.")}
        
        print(f"Thread finished for job_id: {job_id}, status: {JOBS[job_id]['status']}")

    except Exception as e:
        import traceback
        print(f"An unhandled exception occurred in thread for job {job_id}: {e}")
        traceback.print_exc()
        JOBS[job_id] = {"status": "error", "message": str(e)}

# --- API Routes ---

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

    template_content = None
    if template_id:
        template = Template.query.get(template_id)
        if template:
            template_content = template.content
        else:
            return jsonify({"error": "Template not found"}), 404

    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    # URL validation (ensure this regex is correct) - Temporarily disabled for debugging
    # url_pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+(?:&[\w-]+=["w-]+)*

    job_id = str(uuid.uuid4())
    
    # Pass the template_content to the analysis function
    thread = threading.Thread(
        target=run_analysis_in_background,
        args=(job_id, run_analysis_for_url, url, title, language, job_id, template_content, user_additional_prompt)
    )
    thread.start()
    
    # Immediately return the job_id
    return jsonify({"job_id": job_id}), 202

@app.route('/api/start-topic-search', methods=['POST'])
def start_topic_search():
    """
    Starts the analysis for a topic search.
    Returns a job_id to the client for polling the result.
    """
    data = request.get_json()
    query = data.get('query')
    process_audio = data.get('process_audio', True)
    search_mode = data.get('search_mode', 'divergent')
    search_language = data.get('search_language', 'zh')
    template_id = data.get('template_id') # Get template_id
    user_additional_prompt = data.get('user_additional_prompt') # Get user_additional_prompt

    template_content = None
    if template_id:
        template = Template.query.get(template_id)
        if template:
            template_content = template.content
        else:
            return jsonify({"error": "Template not found"}), 404

    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    job_id = str(uuid.uuid4())
    
    # Pass the template_content to the analysis function
    thread = threading.Thread(
        target=run_analysis_in_background,
        args=(job_id, run_analysis, query, process_audio, search_mode, search_language, job_id, template_content, user_additional_prompt)
    )
    thread.start()
    
    # Remove this line as it is outside of any function and causes a syntax error.


@app.route('/api/get-job-result/<job_id>')
def get_job_result(job_id):
    """
    Pollable endpoint for the frontend to get the status and result of a job.
    """
    job = JOBS.get(job_id)
    
    if not job:
        return jsonify({"status": "not_found"}), 404
    
    if job['status'] == 'success':
        result_data = job.get('result', {})
        
        # Differentiate between single URL and topic search results
        if 'final_content' in result_data and 'individual_summaries' in result_data:
            # This is a result from `run_analysis` (topic search), which is already in the correct format.
            # individual_summaries now contains full_transcript
            formatted_result = result_data
        else:
            # This is a result from `run_analysis_for_url` (single URL). Format it.
            # It now directly returns summary and full_transcript
            formatted_result = {
                "title": result_data.get("title"),
                "url": result_data.get("url"),
                "summary": result_data.get("summary"),
                "full_transcript": result_data.get("full_transcript")
            }
        
        return jsonify({"status": "success", "data": formatted_result})

    else:
        # Return other statuses like 'running', 'error', 'starting'
        return jsonify(job)

# --- Template Management API ---
@app.route('/api/templates', methods=['POST'])
def create_template():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')

    if not name or not content:
        return jsonify({"error": "Template name and content are required"}), 400

    template = Template(name=name, content=content) # No user_id for now
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

    db.session.delete(template)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    # IMPORTANT: use_reloader=False is critical to prevent the server from
    # restarting when background threads write output files.
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)