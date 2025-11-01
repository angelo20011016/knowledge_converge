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
# Set to True to simulate AI processing without making actual API calls.
# Set to False to enable actual AI processing (requires GEMINI_API_API_KEY in .env).
SIMULATE_AI_PROCESSING = False

# --- Base Output Directory ---
BASE_OUTPUT_DIR = Path(__file__).parent / "output"
# Ensure the base output directory exists
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Add subdirectories to Python path ---
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, 'step1_get_10url'))
sys.path.append(os.path.join(current_dir, 'modules'))
sys.path.append(os.path.join(current_dir, 'step3_AI_summary'))


# --- Import functions from our modules ---
from yt_get_cc import get_subtitle
from download_YTvideo2wav import download_audio
from yt_transcription_re import clean_vtt_file
from transcribe_wav import transcribe_audio_single # Re-add the correct async transcriber

# Import new AI processing modules
from analyze_transcript_with_gemini import analyze_transcript_with_gemini


async def translate_query(query: str) -> str:
    if all(ord(c) < 128 for c in query):
        print(f"Query '{query}' appears to be English, skipping translation.")
        return query
    try:
        translator = Translator()
        # Lazy import to avoid issues with dependencies on startup
        from googletrans import Translator, LANGUAGES
        detection = translator.detect(query)
        source_lang = detection.lang
        # Force source language to Chinese for better accuracy
        translated = translator.translate(query, src='zh-TW', dest='en')
        print(f"Translated '{query}' from {LANGUAGES.get(source_lang, 'Unknown')} to English: '{translated.text}'")
        return translated.text
    except Exception as e:
        print(f"Translation failed: {e}. Using original query.")
        return query

import yt_dlp
import re

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
        
        # Create a safe folder name from the title
        safe_folder_name = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        print(f"Fetched video info: ID='{video_id}', Title='{title}'")
        return {"video_id": video_id, "title": title, "safe_folder_name": safe_folder_name}
    except Exception as e:
        print(f"Error fetching video info from URL {url} using yt-dlp: {e}", file=sys.stderr)
        return None

async def run_analysis_for_url(url: str, title: str | None = None, language: str = 'en', job_id: str | None = None, template_content: str | None = None, user_additional_prompt: str | None = None):
    """
    Runs the analysis pipeline for a single YouTube URL.
    Accepts an optional title; if not provided, it will be fetched from YouTube.
    Returns a dictionary with status and result.
    """
    print(f"--- run_analysis_for_url: START for job {job_id} ({url}) ---")
    start_time = time.time()
    
    audio_path = None  # Define audio_path here to be accessible in finally block

    try:
        # --- 1. Fetch Video Info & Prepare Directories ---
        video_info = get_video_info_from_url(url)
        if not video_info:
            raise ValueError("Invalid YouTube URL or failed to fetch video info.")
        
        video_id = video_info["video_id"]
        video_title = title or video_info["title"]
        
        if job_id:
            question_dir = BASE_OUTPUT_DIR / 'jobs' / job_id
        else:
            safe_folder_name = "".join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
            question_dir = BASE_OUTPUT_DIR / 'Single_URL' / safe_folder_name

        subs_dir = question_dir / 'subs'
        audio_dir = question_dir / 'audio_files'
        transcripts_dir = question_dir / 'transcripts'
        summary_dir = question_dir / 'summary'

        os.makedirs(subs_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(summary_dir, exist_ok=True)

        transcript_path = None

        # --- 2. Try to get official subtitles ---
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

        # --- 3. If no transcript from subtitles, process audio ---
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

        # --- 4. Analyze the final transcript ---
        if not transcript_path:
            raise Exception("Could not generate a transcript from subtitles or audio.")

        print("Analyzing final transcript...")
        summary_content = ""
        final_analysis_path = ""

        if not SIMULATE_AI_PROCESSING:
            analysis_result = analyze_transcript_with_gemini(transcript_path, template_content, user_additional_prompt)
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
            # Simulate analysis
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
        print(f"An error occurred in run_analysis_for_url for job {job_id}: {e}", file=sys.stderr)
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