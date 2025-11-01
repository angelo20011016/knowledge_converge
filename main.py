import json
import os
import sys
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import yt_dlp
import re

# --- Configuration for AI Processing ---
SIMULATE_AI_PROCESSING = False

# --- Base Output Directory ---
BASE_OUTPUT_DIR = Path(__file__).parent / "output"
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Add subdirectories to Python path ---
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, 'modules'))
sys.path.append(os.path.join(current_dir, 'step3_AI_summary'))

# --- Import functions from our modules ---
from yt_get_cc import get_subtitle
from download_YTvideo2wav import download_audio
from yt_transcription_re import clean_vtt_file
from transcribe_wav import transcribe_audio_single
from analyze_transcript_with_gemini import analyze_transcript_with_gemini

def get_video_info_from_url(url: str) -> dict | None:
    """Fetches video title and ID from a YouTube URL using yt-dlp."""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get('id', None)
            title = info_dict.get('title', None)
            if not video_id or not title:
                raise ValueError("Could not extract video ID or title.")
        
        safe_folder_name = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        print(f"Fetched video info: ID='{video_id}', Title='{title}'")
        return {"video_id": video_id, "title": title, "safe_folder_name": safe_folder_name}
    except Exception as e:
        print(f"Error fetching video info from URL {url} using yt-dlp: {e}", file=sys.stderr)
        return None

async def run_analysis_for_url(user_id: int, url: str, title: str | None = None, language: str = 'en', template_content: str | None = None, user_additional_prompt: str | None = None):
    """
    Runs the analysis pipeline for a single YouTube URL.
    Returns a dictionary with status and result.
    """
    print(f"--- run_analysis_for_url: START for URL ({url}) by user_id ({user_id}) ---")
    start_time = time.time()
    
    audio_path = None

    try:
        video_info = get_video_info_from_url(url)
        if not video_info:
            raise ValueError("Invalid YouTube URL or failed to fetch video info.")
        
        video_id = video_info["video_id"]
        video_title = title or video_info["title"]
        
        safe_folder_name = "".join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
        # Incorporate user_id into the output path
        question_dir = BASE_OUTPUT_DIR / 'Single_URL' / str(user_id) / safe_folder_name

        subs_dir = question_dir / 'subs'
        audio_dir = question_dir / 'audio_files'
        transcripts_dir = question_dir / 'transcripts'
        summary_dir = question_dir / 'summary'

        os.makedirs(subs_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(summary_dir, exist_ok=True)

        transcript_path = None

        print("Checking for official subtitles...")
        lang_prefs = ['zh-Hant', 'zh-TW', 'zh'] if language == 'zh' else ['en', 'en-US']
        try:
            subtitle_path = get_subtitle(url, output_dir=str(subs_dir), lang_prefs=lang_prefs)
            if subtitle_path:
                print(f"Official subtitle downloaded: {subtitle_path}")
                cleaned_path = clean_vtt_file(subtitle_path, output_dir=str(transcripts_dir))
                transcript_path = cleaned_path
                print(f"Official subtitle cleaned and saved to: {transcript_path}")
            else:
                print("No suitable official subtitle found.")
        except Exception as e:
            print(f"Warning: Subtitle processing failed: {e}. Proceeding to audio download.", file=sys.stderr)

        if not transcript_path:
            print("Downloading and transcribing audio...")
            audio_path = download_audio(url, output_dir=str(audio_dir))
            if audio_path:
                print(f"Audio downloaded successfully: {audio_path}")
                transcript_path = await transcribe_audio_single(
                    audio_path=audio_path,
                    output_dir=str(transcripts_dir),
                    language=language
                )
                print(f"Audio transcribed successfully: {transcript_path}")
            else:
                raise Exception("Audio download failed to return a valid path.")

        if not transcript_path:
            raise Exception("Could not generate a transcript from subtitles or audio.")

        print("Analyzing final transcript...")
        summary_content = ""
        final_analysis_path = ""

        if not SIMULATE_AI_PROCESSING:
            analysis_result = analyze_transcript_with_gemini(transcript_path, template_content, user_additional_prompt)
            
            if analysis_result.get("error"):
                raise Exception(f"AI analysis failed: {analysis_result['error']}")

            final_analysis_path = analysis_result.get("analysis_path")
            summary_content = analysis_result.get("summary_content")
            full_transcript_content = analysis_result.get("transcript_content")

            if not final_analysis_path or not Path(final_analysis_path).is_file():
                 raise FileNotFoundError(f"Could not find the generated analysis file at {final_analysis_path}")
            if not summary_content:
                raise ValueError("AI analysis did not return summary content.")
            if not full_transcript_content:
                raise ValueError("AI analysis did not return full transcript content.")
        else:
            transcript_filename = Path(transcript_path).stem
            final_analysis_path = summary_dir / f"{transcript_filename}_summary.txt"
            summary_content = f"[Simulated] Analysis for {video_title}"
            with open(final_analysis_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            print(f"Simulated AI analysis for {transcript_path}")

        end_time = time.time()
        print(f"--- Total Execution Time: {end_time - start_time:.2f} seconds ---")
        
        return {
            "status": "success",
            "result": {
                "title": video_title,
                "url": url,
                "summary": summary_content,
                "final_content_path": str(final_analysis_path),
                "full_transcript": full_transcript_content
            }
        }

    except Exception as e:
        import traceback
        print(f"An error occurred in run_analysis_for_url for url {url}: {e}", file=sys.stderr)
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                print(f"Cleaning up audio file: {audio_path}")
                os.remove(audio_path)
            except OSError as e:
                print(f"Error removing audio file {audio_path}: {e}", file=sys.stderr)
