import librosa
from faster_whisper import WhisperModel
from pathlib import Path
import time
import traceback # Added import
import sys # Added import for sys.stderr

def transcribe_audio_single(audio_path: str, output_dir: str, language: str = "zh", model_params: dict = None) -> str | None:
    """
    Transcribes a single audio file using faster-whisper.

    Args:
        audio_path: Path to the input audio file.
        output_dir: Directory to save the final transcript file.
        language: Language of the audio for transcription.
        model_params: Dictionary of parameters for the WhisperModel.

    Returns:
        The path to the transcript file, or None if an error occurs.
    """
    if model_params is None:
        model_params = {"model_size_or_path": "base", "device": "cuda", "compute_type": "int8"}

    print("--- Single-threaded Transcription Start ---")
    
    try:
        # --- 1. Load Model ---
        load_model_start_time = time.time()
        print(f"Loading Whisper model ({model_params.get('model_size_or_path', 'default')})...")
        model = WhisperModel(**model_params)
        print(f"Model loaded in {time.time() - load_model_start_time:.2f}s.")

        # --- 2. Load Audio ---
        load_audio_start_time = time.time()
        print(f"Loading audio file: {audio_path}...")
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        print(f"Audio loaded in {time.time() - load_audio_start_time:.2f}s.")

        # --- 3. Transcribe Audio ---
        print(f"Starting transcription in language: {language}...")
        # The transcribe function returns a generator. The actual transcription happens when we iterate over it.
        segments_generator, info = model.transcribe(audio, language=language ,without_timestamps=True)

        # --- 4. Process and Save Transcript ---
        # We will iterate over the segments, which is the actual transcription process.
        # This provides real-time feedback instead of making it look like it's hanging.
        save_text_start_time = time.time()
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        transcript_file_path = output_path / (Path(audio_path).stem + "_transcript.txt")
        
        print("Processing and writing segments to file...")
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments_generator):
                segment_text = seg.text.strip()
                f.write(segment_text + " ")
                print(f"  - Transcribed segment {i+1}: {segment_text}")

        print(f"Transcription and saving completed in {time.time() - save_text_start_time:.2f}s.")
        print(f"Full transcript saved to: {transcript_file_path}")
        
        return str(transcript_file_path)

    except Exception as e:
        print(f"An error occurred during single-threaded transcription: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr) # Print the full traceback
        return None

if __name__ == '__main__':
    import os
    # Example usage for standalone testing
    test_audio_file = r"D:\\projects\\loacl_STT\\audio_files\\一期视频看懂人形机器人_下一个万亿赛道_专访安克创新CEO陽萌_大咖谈芯第15期.wav"
    test_output_dir = "transcripts_test"
    
    if os.path.exists(test_audio_file):
        print(f"--- Running standalone test for transcribe_wav.py ---")
        transcribe_audio_single(
            audio_path=test_audio_file,
            output_dir=test_output_dir,
            language="zh",
            model_params={"model_size_or_path": "base", "device": "cuda", "compute_type": "int8"}
        )
    else:
        print(f"Test audio file not found, skipping example run: {test_audio_file}")
