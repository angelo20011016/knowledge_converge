import yt_dlp
import os
from pathlib import Path
import re
import sys
import time
from yt_dlp import utils

def sanitize_filename(name: str) -> str:
    """Replaces unsafe characters in a filename with underscores."""
    return re.sub(r'[^\w\d.-]+', '_', name)

def download_audio(url: str, output_dir: str, ffmpeg_path: str = None, concurrent_fragments: int = 8) -> str | None:
    """
    Downloads audio from a YouTube URL, converts it to WAV, and saves it.
    Includes retry logic for HTTP 429 errors.

    Args:
        url: The YouTube URL to download.
        output_dir: The directory to save the WAV file.
        ffmpeg_path: Optional path to the FFmpeg executable.
        concurrent_fragments: The number of concurrent fragments to download to speed up the process.

    Returns:
        The full path to the saved WAV file, or None if an error occurred.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'quiet': True, # yt-dlp itself will be quiet, aria2 will show progress
        'no_warnings': True,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M'],
    }

    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path

    max_retries = 3
    base_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                original_filepath = ydl.prepare_filename(info_dict)
                wav_filepath = original_filepath.rsplit('.', 1)[0] + '.wav'

                if not os.path.exists(wav_filepath):
                    # This can happen if the file has a different extension before conversion
                    # Let's find the created .wav file by checking the output directory
                    for f in Path(output_dir).glob(f"{Path(ydl.prepare_filename(info_dict)).stem}*.wav"):
                        wav_filepath = str(f)
                        break
                    if not os.path.exists(wav_filepath):
                        print(f"Error: Converted WAV file not found.", file=sys.stderr)
                        return None

                safe_name = sanitize_filename(Path(wav_filepath).name)
                safe_filepath = os.path.join(output_dir, safe_name)

                # Use os.replace to atomically replace if target exists, or rename if not.
                # This handles WinError 183 (file exists) by overwriting.
                try:
                    os.replace(wav_filepath, safe_filepath)
                except Exception as rename_e:
                    print(f"Warning: Could not rename {wav_filepath} to {safe_filepath}: {rename_e}", file=sys.stderr)
                    # If rename fails, try to copy and delete original, or just use original path
                    # For now, let's assume os.replace is robust enough.
                    # If it still fails, the original wav_filepath might be valid.
                    safe_filepath = wav_filepath # Fallback to original path if rename fails

                if os.path.getsize(safe_filepath) < 1024: # 1 KB threshold
                    print(f"Warning: Audio file may be empty: {safe_filepath}", file=sys.stderr)
                
                return safe_filepath

        except utils.DownloadError as e:
            if "HTTP Error 429" in str(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Warning: Download failed with HTTP 429. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Error downloading or converting audio for {url}: {e}", file=sys.stderr)
                raise e
        except Exception as e:
            print(f"An unexpected error occurred in download_audio: {e}", file=sys.stderr)
            raise e
            
    return None

if __name__ == '__main__':
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"Testing audio download for URL: {test_url}")
    
    downloaded_file = download_audio(test_url, output_dir="temp_audio")
    
    if downloaded_file:
        print(f"Successfully downloaded audio to: {downloaded_file}")
        try:
            os.remove(downloaded_file)
            os.rmdir("temp_audio")
            print("Cleaned up temporary files.")
        except OSError as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
    else:
        print("Failed to download audio.")