import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

def analyze_transcript_with_gemini(transcript_path: str):
    load_dotenv() # Load environment variables from .env
    api_key = os.getenv("GEMINI_API_KEY") # Assuming GEMINI_API_KEY is set in .env
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return

    genai.configure(api_key=api_key)

    # Use the model name as specified by the user
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file not found at {transcript_path}")
        return

    # Prompt for content analysis and extraction of useful information
    analysis_prompt = f"""請對以下文字進行內容分析和整理，提取出對我有用的資訊。請以條列式或結構化的方式呈現，並確保資訊的實用性。

{transcript_content}"""

    # Generate analysis
    try:
        print(f"Analyzing content for {transcript_path}...")
        analysis_response = model.generate_content(analysis_prompt)
        analysis_text = analysis_response.text
        print("Content analysis generated.")
    except Exception as e:
        print(f"Error generating content analysis: {e}")
        analysis_text = ""

    # Determine output directory
    transcript_path_obj = Path(transcript_path)
    video_id = transcript_path_obj.stem # Gets 'video_id_123' from 'video_id_123.txt'
    
    # The new subfolder will be 'summary/video_id_123/' under the question's base directory
    # Assuming transcript_path is like '.../Question/Simulated_Topic_For_Testing/transcripts/video_id_123.txt'
    # We want to create '.../Question/Simulated_Topic_For_Testing/summary/video_id_123/'
    question_base_dir = transcript_path_obj.parent.parent # This gets to 'Simulated_Topic_For_Testing'
    summary_base_dir = question_base_dir / 'summary'
    # No need for an intermediate directory named after video_id
    # The output file will be directly in the summary directory
    analysis_file_path = summary_base_dir / f"{video_id}_summary.txt"
    # Ensure the summary directory exists (this might be redundant if main.py already creates it)
    os.makedirs(summary_base_dir, exist_ok=True)

    # Save analysis

    with open(analysis_file_path, 'w', encoding='utf-8') as f:
        f.write(analysis_text)
    print(f"Analysis saved to {analysis_file_path}")

    return {"analysis_path": str(analysis_file_path)}

if __name__ == "__main__":
    # Example usage (replace with actual path for testing)
    # This assumes you have a dummy transcript file at this path
    dummy_transcript_path_1 = "/Users/angelo/myproject/knowledge_converge/Question/Simulated_Topic_For_Testing/transcripts/video_id_123.txt"
    print(f"Running example for {dummy_transcript_path_1}")
    analyze_transcript_with_gemini(dummy_transcript_path_1)

    dummy_transcript_path_2 = "/Users/angelo/myproject/knowledge_converge/Question/Simulated_Topic_For_Testing/transcripts/video_id_456.txt"
    print(f"Running example for {dummy_transcript_path_2}")
    analyze_transcript_with_gemini(dummy_transcript_path_2)
