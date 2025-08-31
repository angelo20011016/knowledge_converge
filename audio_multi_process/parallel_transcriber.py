import librosa
from faster_whisper import WhisperModel
from pathlib import Path
import time
import multiprocessing
import os

def _split_audio_into_chunks(audio_path: str, num_chunks: int, target_sr: int):
    """Helper function to split audio into chunks."""
    audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    total_samples = len(audio)
    chunk_samples = total_samples // num_chunks
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_samples
        end = total_samples if i == num_chunks - 1 else (i + 1) * chunk_samples
        chunk_audio = audio[start:end]
        chunks.append(chunk_audio)
    return chunks, sr

def _transcribe_chunk(chunk_audio, sr, chunk_index, model_params, language="zh"):
    """Helper function to transcribe a single audio chunk."""
    pid = multiprocessing.current_process().pid
    start_time = time.time()
    print(f"[{pid}] Start transcription for chunk {chunk_index} in language '{language}'")

    model = WhisperModel(**model_params)
    segments, _ = model.transcribe(chunk_audio, language=language, vad_filter=True)

    full_text = " ".join(seg.text.strip() for seg in segments)
    
    end_time = time.time()
    print(f"[{pid}] Finished transcription for chunk {chunk_index} in {end_time - start_time:.2f}s")
    return full_text

def parallel_transcribe_audio(audio_path: str, output_dir: str, num_chunks=3, model_params=None, language="zh", target_sr=16000) -> str | None:
    """
    Transcribes an audio file in parallel by splitting it into chunks.
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
    try:
        base_filename = Path(audio_path).stem
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        audio_chunks, sr = _split_audio_into_chunks(audio_path, num_chunks, target_sr)

        tasks = []
        for idx, chunk_audio in enumerate(audio_chunks):
            tasks.append((chunk_audio, sr, idx, model_params, language))

        start_total = time.time()
        # Using maxtasksperchild=1 to ensure child processes are recycled.
        # This can help prevent hangs related to CUDA/GPU resource management in subprocesses.
        with multiprocessing.Pool(processes=num_chunks, maxtasksperchild=1) as pool:
            results = pool.starmap(_transcribe_chunk, tasks)
        end_total = time.time()

        # Combine all transcribed text chunks
        full_transcript = " ".join(results).strip()

        # Save the final merged transcript
        final_path = output_path / f"{base_filename}_full_transcript.txt"
        final_path.write_text(full_transcript, encoding="utf-8")

        print(f"[INFO] Full transcript saved to {final_path}")
        print(f"[INFO] Total execution time: {end_total - start_total:.2f} seconds")
        return str(final_path)

    except Exception as e:
        print(f"An error occurred during parallel transcription: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    # This needs to be inside the __main__ guard for multiprocessing to work correctly on Windows
    multiprocessing.freeze_support()

    # Example usage
    input_audio_file = r"D:\projects\loacl_STT\audio_files\一期视频看懂人形机器人_下一个万亿赛道_专访安克创新CEO阳萌_大咖谈芯第15期.wav"
    output_dir_test = r"D:\projects\loacl_STT\Video_Knowledge_Convergence\audio_multi_process\processed_audio"

    # Check if the dummy file exists, otherwise skip the test
    if os.path.exists(input_audio_file):
        model_params_test = {
            "model_size_or_path": "base",
            "device": "cuda",
            "compute_type": "int8"
        }

        parallel_transcribe_audio(
            audio_path=input_audio_file,
            output_dir=output_dir_test,
            num_chunks=3,
            model_params=model_params_test,
            language="zh"
        )
    else:
        print(f"Test audio file not found, skipping example run: {input_audio_file}")
