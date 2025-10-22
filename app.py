import asyncio
import threading
import uuid
from pathlib import Path
import sys
from flask_cors import CORS
from flask import Flask, request, jsonify
import os

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

    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    job_id = str(uuid.uuid4())
    
    # Pass the job_id to the analysis function
    thread = threading.Thread(
        target=run_analysis_in_background,
        args=(job_id, run_analysis_for_url, url, title, language, job_id)
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

    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    job_id = str(uuid.uuid4())
    
    thread = threading.Thread(
        target=run_analysis_in_background,
        args=(job_id, run_analysis, query, process_audio, search_mode, search_language, job_id)
    )
    thread.start()
    
    return jsonify({"job_id": job_id}), 202


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
            formatted_result = result_data
        else:
            # This is a result from `run_analysis_for_url` (single URL). Format it.
            summary_item = {
                "title": result_data.get("title"),
                "url": result_data.get("url"),
                "summary": result_data.get("summary")
            }
            formatted_result = {
                "final_content": result_data.get("summary"),
                "individual_summaries": [summary_item] if summary_item.get("summary") else []
            }
        
        return jsonify({"status": "success", "data": formatted_result})

    else:
        # Return other statuses like 'running', 'error', 'starting'
        return jsonify(job)

if __name__ == '__main__':
    # IMPORTANT: use_reloader=False is critical to prevent the server from
    # restarting when background threads write output files.
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)
