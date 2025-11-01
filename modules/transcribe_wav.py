import os
import google.generativeai as genai
from pathlib import Path
import time
from dotenv import load_dotenv
import asyncio
from pydub import AudioSegment
import tempfile

# --- Load environment variables ---
load_dotenv()

# Define chunk length in milliseconds (e.g., 60 seconds)
CHUNK_LENGTH_MS = 60 * 1000

async def transcribe_audio_single(audio_path: str, output_dir: str, language: str = "zh", model_params: dict = None) -> str | None:
    """
    Transcribes a single audio file asynchronously using the Gemini API by chunking the audio.

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

        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        
        prompt = (
            "Please provide a complete and accurate transcript of the audio provided. "
            "The audio is in {language}. "
            "Do not add any comments, summaries, or extra text—only the spoken words."
        ).format(language=language)

        # --- 2. Load Audio File and Chunk ---
        print(f"Loading audio file for chunking: {Path(audio_path).name}...")
        audio = AudioSegment.from_wav(audio_path)
        total_length_ms = len(audio)
        
        all_chunk_transcripts = []
        tasks = []
        
        for i in range(0, total_length_ms, CHUNK_LENGTH_MS):
            chunk_start_ms = i
            chunk_end_ms = min(i + CHUNK_LENGTH_MS, total_length_ms)
            chunk = audio[chunk_start_ms:chunk_end_ms]
            
            # Create a temporary file for each chunk
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_chunk_file:
                chunk_file_path = Path(temp_chunk_file.name)
                chunk.export(chunk_file_path, format="wav")
            
            print(f"Transcribing chunk {i // CHUNK_LENGTH_MS + 1} ({(chunk_end_ms - chunk_start_ms) / 1000:.1f}s)...")
            
            async def transcribe_chunk(chunk_path, current_prompt):
                with open(chunk_path, "rb") as f:
                    chunk_audio_data = f.read()
                chunk_audio_file_data = {
                    'mime_type': 'audio/wav',
                    'data': chunk_audio_data
                }
                response = await model.generate_content_async(
                    [current_prompt, chunk_audio_file_data],
                    request_options={"timeout": 900}
                )
                os.remove(chunk_path) # Clean up temporary chunk file
                return response.text

            tasks.append(transcribe_chunk(chunk_file_path, prompt))

        chunk_results = await asyncio.gather(*tasks)
        all_chunk_transcripts = [result for result in chunk_results if result] # Filter out any empty results
        
        full_transcript = " ".join(all_chunk_transcripts)
        
        # --- 3. Save Full Transcript ---
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        transcript_file_path = output_path / (Path(audio_path).stem + "_transcript.txt")
        
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(full_transcript)
            
        print(f"Saved full transcript for {Path(audio_path).name} to: {transcript_file_path}")
        
        return str(transcript_file_path)

    except Exception as e:
        import traceback
        print(f"An error occurred during async Gemini transcription for {Path(audio_path).name}: {e}")
        traceback.print_exc()
        raise e

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
