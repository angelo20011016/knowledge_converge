import os
import google.generativeai as genai
from pathlib import Path
import time
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

def transcribe_audio_single(audio_path: str, output_dir: str, language: str = "zh", model_params: dict = None) -> str | None:
    """
    Transcribes a single audio file using the Gemini API.

    Args:
        audio_path: Path to the input audio file (.wav).
        output_dir: Directory to save the final transcript file.
        language: Language of the audio for transcription (e.g., "zh" for Chinese, "en" for English).
                  This is used in the prompt for the Gemini model.
        model_params: (Not used for Gemini) Kept for compatibility with the main script's function call.

    Returns:
        The path to the transcript file, or None if an error occurs.
    """
    print("--- Gemini API Transcription Start ---")
    
    try:
        # --- 1. Configure Gemini API ---
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)

        # --- 2. Upload Audio File ---
        upload_start_time = time.time()
        print(f"Uploading audio file to Gemini: {audio_path}...")
        audio_file = genai.upload_file(path=audio_path)
        print(f"File uploaded successfully in {time.time() - upload_start_time:.2f}s. URI: {audio_file.uri}")

        # --- 3. Generate Content (Transcribe) ---
        generation_start_time = time.time()
        print("Sending request to Gemini for transcription...")
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        
        # Constructing a clear prompt for the model
        prompt = (
            "Please provide a complete and accurate transcript of the audio provided. "
            "The audio is in {language}. "
            "Do not add any comments, summaries, or extra text—only the spoken words."
        ).format(language=language)

        response = model.generate_content([prompt, audio_file])
        
        print(f"Transcription received from Gemini in {time.time() - generation_start_time:.2f}s.")

        # --- 4. Save Transcript ---
        save_text_start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        transcript_file_path = output_path / (Path(audio_path).stem + "_transcript.txt")
        
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Transcript saved to: {transcript_file_path} in {time.time() - save_text_start_time:.2f}s.")
        
        return str(transcript_file_path)

    except Exception as e:
        import traceback
        print(f"An error occurred during Gemini transcription: {e}")
        traceback.print_exc()
        return None
if __name__ == '__main__':
    # Example usage for standalone testing
    # Make sure you have a .env file in the project root with your GEMINI_API_KEY
    # !!! 请将下面的路径替换为一个实际存在的 .wav 音频文件路径 !!!
    test_audio_file = r"D:\Video_Knowledge_Convergence_Output\Single_URL\与人合作中的生死疲劳\audio_files\qxDo_QzimTk.wav" 
    test_output_dir = "transcripts_test"
    
    if os.path.exists(test_audio_file):
        print(f"--- Running standalone test for transcribe_wav.py (Gemini) ---")
        transcribe_audio_single(
            audio_path=test_audio_file,
            output_dir=test_output_dir,
            language="zh"
        )
    else:
        print(f"Test audio file not found, skipping example run: {test_audio_file}")