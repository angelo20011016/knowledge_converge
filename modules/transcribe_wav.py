import os
import google.generativeai as genai
from pathlib import Path
import time
from dotenv import load_dotenv
import asyncio

# --- Load environment variables ---
load_dotenv()

async def transcribe_audio_single(audio_path: str, output_dir: str, language: str = "zh", model_params: dict = None) -> str | None:
    """
    Transcribes a single audio file asynchronously using the Gemini API.

    Args:
        audio_path: Path to the input audio file (.wav).
        output_dir: Directory to save the final transcript file.
        language: Language of the audio for transcription.
        model_params: (Not used for Gemini) Kept for compatibility.

    Returns:
        The path to the transcript file, or None if an error occurs.
    """
    print(f"--- Starting async Gemini transcription for: {Path(audio_path).name} ---")
    
    try:
        # --- 1. Configure Gemini API ---
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)

        # --- 2. Upload Audio File ---
        upload_start_time = time.time()
        print(f"Uploading: {Path(audio_path).name}...")
        # Note: The current SDK's upload_file is synchronous.
        # We run it in a thread pool to avoid blocking the asyncio event loop.
        loop = asyncio.get_running_loop()
        audio_file = await loop.run_in_executor(
            None, lambda: genai.upload_file(path=audio_path)
        )
        print(f"Uploaded {Path(audio_path).name} in {time.time() - upload_start_time:.2f}s.")

        # --- 3. Generate Content (Transcribe) ---
        generation_start_time = time.time()
        print(f"Requesting transcription for {Path(audio_path).name}...")
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        prompt = (
            "Please provide a complete and accurate transcript of the audio provided. "
            "The audio is in {language}. "
            "Do not add any comments, summaries, or extra text—only the spoken words."
        ).format(language=language)

        response = await model.generate_content_async(
            [prompt, audio_file],
            request_options={"timeout": 900} # 15-minute timeout
        )
        
        print(f"Received transcript for {Path(audio_path).name} in {time.time() - generation_start_time:.2f}s.")

        # --- 4. Save Transcript ---
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        transcript_file_path = output_path / (Path(audio_path).stem + "_transcript.txt")
        
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Saved transcript for {Path(audio_path).name} to: {transcript_file_path}")
        
        return str(transcript_file_path)

    except Exception as e:
        import traceback
        print(f"An error occurred during async Gemini transcription for {Path(audio_path).name}: {e}")
        # traceback.print_exc() # This can be noisy in parallel runs
        return None

if __name__ == '__main__':
    # Example usage for standalone testing
    async def main_test():
        test_audio_file = r"D:\Video_Knowledge_Convergence_Output\Single_URL\与人合作中的生死疲劳\audio_files\qxDo_QzimTk.wav" 
        test_output_dir = "transcripts_test"
        
        if os.path.exists(test_audio_file):
            print(f"--- Running standalone test for transcribe_wav.py (Gemini) ---")
            await transcribe_audio_single(
                audio_path=test_audio_file,
                output_dir=test_output_dir,
                language="zh"
            )
        else:
            print(f"Test audio file not found, skipping example run: {test_audio_file}")

    asyncio.run(main_test())
