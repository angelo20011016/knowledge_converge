import asyncio
import asyncio
import threading
from pathlib import Path
import sys
from flask_cors import CORS
from flask import Flask, request, jsonify
import re
import json
import os

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

    # --- Logic for Topic Search (handles partial and final results) ---
    if task_type == 'topic':
        question_dir = analysis_context.get("question_dir")
        if not question_dir:
            return jsonify({"status": "error", "message": "Analysis context not found."}), 500
        
        try:
            final_info_path = question_dir / 'final_extracted_info.txt'
            is_complete = final_info_path.is_file()

            final_content = ""
            if is_complete:
                with open(final_info_path, 'r', encoding='utf-8') as f:
                    final_content = f.read()

            # Always check for individual summaries, regardless of completion status
            individual_summaries = []
            summary_dir = question_dir / 'summary'
            urls_json_path = question_dir / 'urls.json'
            
            video_title_map = {}
            if urls_json_path.is_file():
                with open(urls_json_path, 'r', encoding='utf-8') as f:
                    videos_info = json.load(f)
                    video_title_map = {info['video_id']: info for info in videos_info}

            if summary_dir.is_dir():
                summary_files = sorted(summary_dir.glob('*_summary.txt')) # Sort for consistent order
                for summary_file in summary_files:
                    video_id_match = re.match(r"([a-zA-Z0-9_-]+)", summary_file.stem)
                    if video_id_match:
                        video_id = video_id_match.group(1)
                        if video_id in video_title_map:
                            video_info = video_title_map[video_id]
                            with open(summary_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            individual_summaries.append({
                                "title": video_info['title'],
                                "url": video_info['url'],
                                "summary": content
                            })
            
            # Determine status: 'success' only if the final file exists.
            # Otherwise, it's 'running' but we still send the partial data.
            current_api_status = "success" if is_complete else "running"

            return jsonify({
                "status": current_api_status, 
                "final_content": final_content,
                "individual_summaries": individual_summaries
            })

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # --- Logic for Single URL (waits for full result) ---
    elif task_type == 'url':
        result_data = analysis_context.get("result_data")
        if not result_data:
            return jsonify({"status": "running"})
        
        try:
            # result_data is now expected to be a dict with title, url, and summary
            # We will format it to look like the 'topic' search result for consistency
            summary_item = {
                "title": result_data.get("title"),
                "url": result_data.get("url"),
                "summary": result_data.get("summary")
            }
            
            return jsonify({
                "status": "success", 
                "final_content": result_data.get("summary"), # For backward compatibility or main display
                "individual_summaries": [summary_item] if summary_item.get("summary") else []
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "idle"})


def run_analysis_thread(query, process_audio, search_mode, search_language):
    try:
        asyncio.run(run_analysis(query, process_audio=process_audio, search_mode=search_mode, search_language=search_language))
    except Exception as e:
        import traceback
        print(f"An error occurred during analysis: {e}")
        traceback.print_exc()
        current_status["main"] = "Error"
        current_status["sub"] = str(e)

def run_url_analysis_thread(url, title, language):
    global analysis_context
    try:
        # This function now returns a dictionary with all the necessary info
        result = asyncio.run(run_analysis_for_url(url, title=title, language=language))
        analysis_context["result_data"] = result
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
    # Get title from request, default to None if not provided
    title = data.get('title') 
    language = data.get('language', 'en')
    if not url: return jsonify({"error": "URL parameter is missing"}), 400

    current_status.update({"main": "Starting URL Analysis", "sub": "Initializing..."})
    # Pass the title to the thread
    thread = threading.Thread(target=run_url_analysis_thread, args=(url, title, language))
    thread.start()
    return jsonify({"status": "Analysis started"}), 202

@app.route('/analyze', methods=['POST'])
def analyze():
    global analysis_context
    current_status.update({"main": "Idle", "sub": ""})
    
    data = request.get_json()
    query = data.get('query')
    process_audio = data.get('process_audio', True)
    search_mode = data.get('search_mode', 'focused') # Default to focused
    search_language = data.get('search_language', 'zh-TW') # Default to zh-TW

    if not query: return jsonify({"error": "Query parameter is missing"}), 400

    # Calculate question_dir and store it in the context immediately
    safe_folder_name = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
    question_dir = BASE_OUTPUT_DIR / 'Question' / safe_folder_name
    analysis_context.update({"task_type": "topic", "question_dir": question_dir, "result_data": None})

    current_status.update({"main": "Starting Analysis", "sub": "Initializing..."})
    thread = threading.Thread(
        target=run_analysis_thread, 
        args=(query, process_audio, search_mode, search_language)
    )
    thread.start()
    return jsonify({"status": "Analysis started"}), 202

if __name__ == '__main__':
    app.run(debug=True, port=5000)