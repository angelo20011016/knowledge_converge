import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import threading

# Add the project root to the Python path to import main
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from main import run_analysis, run_analysis_for_url, BASE_OUTPUT_DIR
from status import current_status

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# A shared object to hold the context of the current analysis
analysis_context = {"task_type": None, "question_dir": None, "result_data": None}

@app.route('/status')
def get_status():
    # The frontend will now poll get-result, so this is just for status text
    return jsonify(current_status)

@app.route('/')
def index():
    return "Video Knowledge Convergence Backend is running!"

@app.route('/api/get-result')
def get_result():
    task_type = analysis_context.get("task_type")
    if not task_type:
        return jsonify({"status": "idle"})

    # --- Logic for Topic Search (can return partial results) ---
    if task_type == 'topic':
        question_dir = analysis_context.get("question_dir")
        if not question_dir:
            return jsonify({"status": "error", "message": "Analysis context not found."}), 500
        
        try:
            # Check for final summary
            final_content = ""
            final_info_path = question_dir / 'final_extracted_info.txt'
            if final_info_path.is_file():
                with open(final_info_path, 'r', encoding='utf-8') as f:
                    final_content = f.read()

            # Check for individual summaries
            individual_summaries = []
            summary_dir = question_dir / 'summary'
            urls_json_path = question_dir / 'urls.json'
            
            video_title_map = {}
            if urls_json_path.is_file():
                with open(urls_json_path, 'r', encoding='utf-8') as f:
                    videos_info = json.load(f)
                    video_title_map = {info['video_id']: info for info in videos_info}

            if summary_dir.is_dir():
                summary_files = summary_dir.glob('*_summary.txt')
                for summary_file in summary_files:
                    video_id = summary_file.stem.split('_')[0]
                    if video_id in video_title_map:
                        video_info = video_title_map[video_id]
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        individual_summaries.append({
                            "title": video_info['title'],
                            "url": video_info['url'],
                            "summary": content
                        })
            
            return jsonify({
                "status": "success", 
                "final_content": final_content,
                "individual_summaries": individual_summaries
            })

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # --- Logic for Single URL (waits for full result) ---
    elif task_type == 'url':
        result_data = analysis_context.get("result_data")
        if not result_data:
             # This case happens while the URL analysis is running
            return jsonify({"status": "running"})
        
        # Once result_data is populated, process it
        try:
            final_content = ""
            final_info_path = result_data.get("final_extracted_info_path")
            if final_info_path and Path(final_info_path).is_file():
                with open(final_info_path, 'r', encoding='utf-8') as f:
                    final_content = f.read()
            return jsonify({"status": "success", "final_content": final_content, "individual_summaries": []})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "idle"})


def run_analysis_thread(query):
    run_analysis(query)

def run_url_analysis_thread(url, language):
    global analysis_context
    try:
        analysis_context["result_data"] = run_analysis_for_url(url, language=language)
    except Exception as e:
        current_status["main"] = "Error"
        current_status["sub"] = str(e)

@app.route('/api/summarize-url', methods=['POST'])
def summarize_url():
    global analysis_context
    current_status.update({"main": "Idle", "sub": ""})
    analysis_context.update({"task_type": "url", "question_dir": None, "result_data": None})
    
    data = request.get_json()
    url = data.get('url')
    language = data.get('language', 'en')
    if not url: return jsonify({"error": "URL parameter is missing"}), 400

    current_status.update({"main": "Starting URL Analysis", "sub": "Initializing..."})
    thread = threading.Thread(target=run_url_analysis_thread, args=(url, language))
    thread.start()
    return jsonify({"status": "Analysis started"}), 202

@app.route('/analyze', methods=['POST'])
def analyze():
    global analysis_context
    current_status.update({"main": "Idle", "sub": ""})
    
    data = request.get_json()
    query = data.get('query')
    if not query: return jsonify({"error": "Query parameter is missing"}), 400

    # Calculate question_dir and store it in the context immediately
    safe_folder_name = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
    question_dir = BASE_OUTPUT_DIR / 'Question' / safe_folder_name
    analysis_context.update({"task_type": "topic", "question_dir": question_dir, "result_data": None})

    current_status.update({"main": "Starting Analysis", "sub": "Initializing..."})
    thread = threading.Thread(target=run_analysis_thread, args=(query,))
    thread.start()
    return jsonify({"status": "Analysis started"}), 202

if __name__ == '__main__':
    app.run(debug=True, port=5000)