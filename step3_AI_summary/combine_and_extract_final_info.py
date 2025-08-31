import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

def combine_and_extract_final_info(question_base_dir: str):
    load_dotenv() # Load environment variables from .env
    api_key = os.getenv("GEMINI_API_KEY") # Assuming GEMINI_API_KEY is set in .env
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return

    genai.configure(api_key=api_key)

    # Use the model name as specified by the user
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    question_base_path = Path(question_base_dir)
    summary_base_dir = question_base_path / 'summary'

    if not summary_base_dir.exists():
        print(f"Error: Summary directory not found at {summary_base_dir}")
        return

    combined_analysis_content = []
    # Find all analysis.txt files in subdirectories of summary_base_dir
    for analysis_file in summary_base_dir.glob('*.txt'):
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                combined_analysis_content.append(f.read())
            print(f"Read analysis from {analysis_file}")
        except Exception as e:
            print(f"Error reading {analysis_file}: {e}")

    if not combined_analysis_content:
        print("No individual analysis files found to combine.")
        return

    full_combined_text = "\n\n---\n\n".join(combined_analysis_content)

    # Define prompt for final extraction of important information and excerpts
    final_extraction_prompt = f"""請根據以下多個分析結果，提取出重要的資訊和節錄。請以條列式或結構化的方式呈現，並確保資訊的精煉和實用性。\n\n{full_combined_text}"""

    # Generate final extraction
    try:
        print("Generating final extracted information...")
        final_extraction_response = model.generate_content(final_extraction_prompt)
        final_extraction_text = final_extraction_response.text
        print("Final extracted information generated.")
    except Exception as e:
        print(f"Error generating final extracted information: {e}")
        final_extraction_text = ""

    # Save final extracted information
    final_extraction_file_path = question_base_path / 'final_extracted_info.txt'
    with open(final_extraction_file_path, 'w', encoding='utf-8') as f:
        f.write(final_extraction_text)
    print(f"Final extracted information saved to {final_extraction_file_path}")

    return {"final_extraction_path": str(final_extraction_file_path)}

if __name__ == "__main__":
    # Example usage (replace with actual path for testing)
    # This assumes you have run analyze_transcript_with_gemini.py for some transcripts first
    dummy_question_dir = "/Users/angelo/myproject/knowledge_converge/Question/Simulated_Topic_For_Testing"
    print(f"Running example for {dummy_question_dir}")
    combine_and_extract_final_info(dummy_question_dir)
