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
        return {"summary_content": None, "transcript_content": None, "analysis_path": None, "error": "GEMINI_API_KEY not set"}

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file not found at {transcript_path}")
        return {"summary_content": None, "transcript_content": None, "analysis_path": None, "error": f"Transcript file not found at {transcript_path}"}

    # --- Prompt Engineering Logic ---
    base_prompt = f"""請對以下文字進行內容分析和整理，提取出對我有用的資訊。請以條列式或結構化的方式呈現，並確保資訊的實用性，最後請務必以Markdown格式進行輸出。"""
    user_custom_prompt = ""
    if template_content:
        user_custom_prompt += template_content
    if user_additional_prompt:
        user_custom_prompt += "\n" + user_additional_prompt
    if user_custom_prompt:
        base_prompt += f"\n\n除了以上要求，使用者還有這些需求：{{{user_custom_prompt}}}"
    analysis_prompt = f"{base_prompt}\n\n以下是需要分析的逐字稿內容：\n{transcript_content}"

    # --- AI Generation ---
    try:
        print(f"Analyzing content for {transcript_path}...")
        analysis_response = model.generate_content(analysis_prompt)
        analysis_text = analysis_response.text
        print("Content analysis generated.")
    except Exception as e:
        print(f"Error generating content analysis: {e}")
        return {"summary_content": None, "transcript_content": transcript_content, "analysis_path": None, "error": str(e)}

    # --- File Output ---
    transcript_path_obj = Path(transcript_path)
    question_base_dir = transcript_path_obj.parent.parent 
    summary_base_dir = question_base_dir / 'summary'
    analysis_file_path = summary_base_dir / f"{transcript_path_obj.stem}_summary.txt"
    os.makedirs(summary_base_dir, exist_ok=True)

    with open(analysis_file_path, 'w', encoding='utf-8') as f:
        f.write(analysis_text)
    print(f"Analysis saved to {analysis_file_path}")

    return {
        "summary_content": analysis_text,
        "transcript_content": transcript_content,
        "analysis_path": str(analysis_file_path)
    }


if __name__ == "__main__":
    # Example usage (for testing purposes)
    dummy_transcript_path = "/path/to/your/dummy/transcript.txt"
    if os.path.exists(dummy_transcript_path):
        print(f"Running example for {dummy_transcript_path}")
        # Test with no custom template
        result_1 = analyze_transcript_with_gemini(dummy_transcript_path)
        print(f"Result 1 (no template): {result_1['summary_content'][:100]}...")
        # Test with a custom template
        my_template = "請將重點整理成一個表格。"
        result_2 = analyze_transcript_with_gemini(dummy_transcript_path, template_content=my_template)
        print(f"Result 2 (with template): {result_2['summary_content'][:100]}...")
    else:
        print(f"Skipping example: dummy transcript file not found at {dummy_transcript_path}")
