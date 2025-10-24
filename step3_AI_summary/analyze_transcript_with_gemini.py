import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

def analyze_transcript_with_gemini(transcript_path: str, template_content: str | None = None, user_additional_prompt: str | None = None):
    load_dotenv() # Load environment variables from .env
    api_key = os.getenv("GEMINI_API_KEY") # Assuming GEMINI_API_KEY is set in .env
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        # Return an error state that main.py can handle
        return {"summary_content": None, "transcript_content": None, "error": "GEMINI_API_KEY not set"}

    genai.configure(api_key=api_key)

    # Use the model name as specified by the user
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file not found at {transcript_path}")
        return {"summary_content": None, "transcript_content": None, "error": f"Transcript file not found at {transcript_path}"}

    # Prompt for content analysis and extraction of useful information
    if template_content:
        base_prompt = template_content
        if user_additional_prompt:
            base_prompt += f"：{user_additional_prompt}"
        analysis_prompt = f"{base_prompt}\n\n以下是需要分析的逐字稿內容：\n{transcript_content}"
    else:
        base_prompt = f"""請對以下文字進行內容分析和整理，提取出對我有用的資訊。請以條列式或結構化的方式呈現，並確保資訊的實用性。"""
        if user_additional_prompt:
            base_prompt += f"：{user_additional_prompt}"
        analysis_prompt = f"{base_prompt}\n\n{transcript_content}"

    # Generate analysis
    try:
        print(f"Analyzing content for {transcript_path}...")
        analysis_response = model.generate_content(analysis_prompt)
        analysis_text = analysis_response.text
        print("Content analysis generated.")
    except Exception as e:
        print(f"Error generating content analysis: {e}")
        # Re-raise or return an error state
        return {"summary_content": None, "transcript_content": transcript_content, "error": str(e)}

    # Determine output directory
    transcript_path_obj = Path(transcript_path)
    video_id = transcript_path_obj.stem # Gets 'video_id_123' from 'video_id_123.txt'
    
    question_base_dir = transcript_path_obj.parent.parent 
    summary_base_dir = question_base_dir / 'summary'
    analysis_file_path = summary_base_dir / f"{video_id}_summary.txt"
    os.makedirs(summary_base_dir, exist_ok=True)

    # Save analysis
    with open(analysis_file_path, 'w', encoding='utf-8') as f:
        f.write(analysis_text)
    print(f"Analysis saved to {analysis_file_path}")

    # Return both summary content and the original transcript content
    return {
        "summary_content": analysis_text,
        "transcript_content": transcript_content,
        "analysis_path": str(analysis_file_path)
    }

if __name__ == "__main__":
    # Example usage (replace with actual path for testing)
    # This assumes you have a dummy transcript file at this path
    dummy_transcript_path_1 = "/Users/angelo/myproject/knowledge_converge/Question/Simulated_Topic_For_Testing/transcripts/video_id_123.txt"
    print(f"Running example for {dummy_transcript_path_1}")
    result_1 = analyze_transcript_with_gemini(dummy_transcript_path_1)
    print(f"Result 1: {result_1}")

    dummy_transcript_path_2 = "/Users/angelo/myproject/knowledge_converge/Question/Simulated_Topic_For_Testing/transcripts/video_id_456.txt"
    print(f"Running example for {dummy_transcript_path_2}")
    result_2 = analyze_transcript_with_gemini(dummy_transcript_path_2)
    print(f"Result 2: {result_2}")
