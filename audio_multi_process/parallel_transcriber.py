import librosa
import soundfile as sf
from faster_whisper import WhisperModel
from pathlib import Path
import time
import multiprocessing
import os
import tempfile
import sys

# Global variable to hold the model instance in each worker process
model_instance = None

def _init_worker(model_params):
    """Initializer for each worker process. Loads the model once."""
    global model_instance
    pid = multiprocessing.current_process().pid
    print(f"[{pid}] Initializing worker and loading model...")
    model_instance = WhisperModel(**model_params)
    print(f"[{pid}] Model loaded.")

def _split_audio_into_temp_files(audio_path: str, num_chunks: int, target_sr: int) -> list[str]:
    """
    Splits the audio into chunks and saves them as temporary files.
    Returns a list of paths to the temporary files.
    """
    print(f"[INFO] Loading and splitting audio into {num_chunks} chunks...")
    audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    total_samples = len(audio)
    chunk_samples = total_samples // num_chunks
    
    temp_files = []
    for i in range(num_chunks):
        start = i * chunk_samples
        end = total_samples if i == num_chunks - 1 else (i + 1) * chunk_samples
        chunk_audio = audio[start:end]
        
        # Create a temporary file and write the chunk to it
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode='w+b')
        sf.write(temp_file.name, chunk_audio, sr)
        temp_files.append(temp_file.name)
        temp_file.close()
        
    print(f"[INFO] Audio split into {len(temp_files)} temporary files.")
    return temp_files, sr

def _transcribe_chunk_from_file(chunk_path: str, chunk_index: int, language: str = "zh") -> str:
    """
    Helper function to transcribe a single audio chunk from a file.
    It uses the pre-loaded global model instance.
    """
    global model_instance
    if model_instance is None:
        raise RuntimeError("Model not initialized in worker process.")

    pid = multiprocessing.current_process().pid
    start_time = time.time()
    print(f"[{pid}] Start transcription for chunk {chunk_index} ('{chunk_path}')")

    segments, _ = model_instance.transcribe(chunk_path, language=language, vad_filter=True)
    full_text = " ".join(seg.text.strip() for seg in segments)
    
    end_time = time.time()
    print(f"[{pid}] Finished transcription for chunk {chunk_index} in {end_time - start_time:.2f}s")
    return full_text

def parallel_transcribe_audio(audio_path: str, output_dir: str, num_chunks=4, model_params=None, language="zh", target_sr=16000) -> str | None:
    """
    Transcribes an audio file in parallel by splitting it into temporary chunk files.
    The transcribed text from all chunks is merged into a single final file.

    Args:
        audio_path: Path to the input audio file.
        output_dir: Directory to save the final transcript file.
        num_chunks: Number of parallel processes to use.
        model_params: Dictionary of parameters for the WhisperModel.
        language: Language of the audio.
        target_sr: Target sample rate for resampling.

    Returns:
        The path to the final transcript file, or None if an error occurs.
    """
    temp_files = []
    try:
        base_filename = Path(audio_path).stem
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Split audio into temporary files instead of in-memory chunks
        temp_files, sr = _split_audio_into_temp_files(audio_path, num_chunks, target_sr)

        # Prepare tasks with file paths instead of raw audio data
        tasks = [(path, idx, language) for idx, path in enumerate(temp_files)]

        start_total = time.time()
        
        # Use an initializer to load the model once per process
        # maxtasksperchild=1 is still useful to release resources, especially GPU memory
        with multiprocessing.Pool(processes=num_chunks, initializer=_init_worker, initargs=(model_params,), maxtasksperchild=1) as pool:
            results = pool.starmap(_transcribe_chunk_from_file, tasks)
            
        end_total = time.time()

        # Combine all transcribed text chunks
        full_transcript = " ".join(results).strip()

        # Save the final merged transcript
        final_path = output_path / f"{base_filename}_full_transcript.txt"
        final_path.write_text(full_transcript, encoding="utf-8")

        print(f"\n[INFO] Full transcript saved to {final_path}")
        print(f"[INFO] Total execution time: {end_total - start_total:.2f} seconds")
        return str(final_path)

    except Exception as e:
        print(f"An error occurred during parallel transcription: {e}", file=sys.stderr)
        return None
    finally:
        # Clean up temporary files
        print("[INFO] Cleaning up temporary audio files...")
        for f in temp_files:
            try:
                os.remove(f)
            except OSError as e:
                print(f"Error removing temp file {f}: {e}", file=sys.stderr)


if __name__ == "__main__":
    # This needs to be inside the __main__ guard for multiprocessing to work correctly on Windows
    multiprocessing.freeze_support()

    # --- Example Usage ---
    # IMPORTANT: Replace this with the actual path to your audio file.
    input_audio_file = r"D:\Video_Knowledge_Convergence_Output\Question\INTJ\audio_files"
    output_dir_test = r".\processed_audio" # Use a relative path for portability

    # Check if the audio file exists, otherwise skip the test
    if os.path.exists(input_audio_file):
        # Parameters for the Whisper model
        # Adjust "model_size_or_path" and "device" based on your hardware.
        # Options for compute_type: "float16", "int8_float16", "int8"
        model_params_test = {
            "model_size_or_path": "base",
            "device": "cuda",
            "compute_type": "int8" # Use "float16" for better accuracy if your GPU supports it
        }

        # Number of parallel processes. A good starting point is the number of CPU cores.
        # If you are GPU-bound, you might need to experiment with this number (e.g., 2-4).
        num_parallel_processes = 4 

        parallel_transcribe_audio(
            audio_path=input_audio_file,
            output_dir=output_dir_test,
            num_chunks=num_parallel_processes,
            model_params=model_params_test,
            language="zh"
        )
    else:
        print("---")
        print(f"ATTENTION: Test audio file not found at '{input_audio_file}'")
        print("Please update the 'input_audio_file' variable in the if __name__ == '__main__': block to run the example.")
        print("---")
