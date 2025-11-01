import json
import os
import sys
import time
import asyncio
from pathlib import Path
from googletrans import Translator, LANGUAGES
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
from get_top_10_watched import get_videos_by_api
from yt_get_cc import get_subtitle
from download_YTvideo2wav import download_audio
from yt_transcription_re import clean_vtt_file
from transcribe_wav import transcribe_audio_single # Re-add the correct async transcriber
from summarize_transcripts import analyze_transcripts
from combine_transcripts import combine_transcripts

# Import new AI processing modules
from analyze_transcript_with_gemini import analyze_transcript_with_gemini
from combine_and_extract_final_info import combine_and_extract_final_info


async def translate_query(query: str) -> str:
    if all(ord(c) < 128 for c in query):
        print(f"Query '{query}' appears to be English, skipping translation.")
        return query
    try:
        translator = Translator()
        detection = translator.detect(query)
        source_lang = detection.lang
        # Force source language to Chinese for better accuracy
        translated = translator.translate(query, src='zh-TW', dest='en')
        print(f"Translated '{query}' from {LANGUAGES.get(source_lang, 'Unknown')} to English: '{translated.text}'")
        return translated.text
    except Exception as e:
        print(f"Translation failed: {e}. Using original query.")
        return query

async def step1_get_urls(query: str, search_mode: str, search_language: str, output_dir: Path) -> str | None:
    """
    Fetches video URLs based on the search mode and saves them to the specified output directory.
    """
    os.makedirs(output_dir, exist_ok=True)

    all_videos = {}  # Use dict for deduplication by video_id
    TOTAL_VIDEOS = 10

    if search_mode == 'focused':
        print(f"\n--- Starting Focused Search for '{query}' (Language: {search_language}) ---")
        try:
            videos = get_videos_by_api(query, lang=search_language, max_results=TOTAL_VIDEOS)
            for video in videos:
                all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': search_language}
            print(f"Found {len(videos)} results.")
        except Exception as e:
            print(f"An error occurred during YouTube API call: {e}")

    else: # Divergent mode
        english_query = await translate_query(query)
        split_results = TOTAL_VIDEOS // 2

        print(f"\n--- Starting Divergent Search for '{query}' (Language: Auto-detect by YouTube) ---")
        try:
            videos = get_videos_by_api(query, max_results=split_results)
            for video in videos:
                all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': 'zh'}
            print(f"Found {len(videos)} results. Total unique videos so far: {len(all_videos)}.")
        except Exception as e:
            print(f"An error occurred during YouTube API call for Chinese query: {e}")

        remaining_results = TOTAL_VIDEOS - len(all_videos)
        if query.lower() != english_query.lower() and remaining_results > 0:
            print(f"\n--- Starting Divergent Search for '{english_query}' (Language: en) ---")
            try:
                videos = get_videos_by_api(english_query, lang='en', max_results=remaining_results)
                for video in videos:
                    all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': 'en'}
                print(f"Found {len(videos)} results. Total unique videos so far: {len(all_videos)}.")
            except Exception as e:
                print(f"An error occurred during YouTube API call for English query: {e}")

    if not all_videos:
        print("No videos found. Aborting.")
        return None

    videos_to_save = [{'video_id': vid, **data} for vid, data in all_videos.items()]
    
    output_filename = output_dir / 'urls.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(videos_to_save, f, ensure_ascii=False, indent=4)

    print(f"\nSuccessfully completed! Found {len(all_videos)} unique videos.")
    print(f"Results saved to {output_filename}")
    return str(output_filename)

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


async def run_analysis(query: str, process_audio: bool = False, search_mode: str = 'divergent', search_language: str = 'zh', job_id: str | None = None, template_content: str | None = None, user_additional_prompt: str | None = None):
    """
    Main analysis pipeline for a given query, adapted for the Job ID system.
    """
    print(f"--- run_analysis: START for job {job_id} ('{query}') ---")
    start_time = time.time()
    downloaded_audio_files = []

    try:
        if not job_id:
            raise ValueError("job_id is required for run_analysis")
        
        job_dir = BASE_OUTPUT_DIR / 'jobs' / job_id
        subs_dir = job_dir / 'subs'
        audio_dir = job_dir / 'audio_files'
        transcripts_dir = job_dir / 'transcripts'
        summary_dir = job_dir / 'summary'

        os.makedirs(job_dir, exist_ok=True)
        os.makedirs(subs_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(summary_dir, exist_ok=True)

        load_dotenv()
        if not os.environ.get("YOUTUBE_API_KEY"):
            print("Warning: 'YOUTUBE_API_KEY' environment variable is not set.")

        urls_json_path = await step1_get_urls(query, search_mode, search_language, output_dir=job_dir)

        if not urls_json_path:
            raise Exception("No videos found for the query.")

        with open(urls_json_path, 'r', encoding='utf-8') as f:
            videos_to_process = json.load(f)

        # --- Separate videos with and without subtitles ---
        videos_with_subs = []
        videos_without_subs = []

        for i, video in enumerate(videos_to_process):
            print(f"\n--- Processing video {i+1}/{len(videos_to_process)}: {video['title']} ---")
            lang_prefs = ['en', 'en-US', 'en-GB'] if video.get('query_lang') == 'en' else ['zh-Hant', 'zh-TW', 'zh', 'zh-Hans']
            try:
                subtitle_path = get_subtitle(video['url'], output_dir=str(subs_dir), lang_prefs=lang_prefs)
                if subtitle_path:
                    cleaned_path = clean_vtt_file(subtitle_path, output_dir=str(transcripts_dir))
                    video['transcript_path'] = cleaned_path
                    videos_with_subs.append(video)
                    print(f"Got transcript from official subtitle: {cleaned_path}")
                else:
                    videos_without_subs.append(video)
            except Exception as e:
                print(f"Subtitle processing failed for {video['title']}: {e}. Adding to audio queue.")
                videos_without_subs.append(video)

        # --- Analyze videos with subtitles first ---
        print(f"\n--- Performing AI Analysis for {len(videos_with_subs)} videos with subtitles ---")
        for video in videos_with_subs:
            if not SIMULATE_AI_PROCESSING:
                analyze_transcript_with_gemini(video['transcript_path'], template_content, user_additional_prompt)
            else:
                sim_path = summary_dir / f"{Path(video['transcript_path']).stem}_summary.txt"
                with open(sim_path, 'w', encoding='utf-8') as f: f.write(f"[Simulated] Analysis for {video['title']}")

        # --- Process videos without subtitles (audio processing) ---
        if process_audio and videos_without_subs:
            print(f"\n--- Batch downloading audio for {len(videos_without_subs)} videos ---")
            # Create callables (functions to be executed) for each download task
            audio_download_tasks = [
                lambda url=v['url'], out=str(audio_dir): download_audio(url, out)
                for v in videos_without_subs
            ]
            # Run download tasks in parallel threads
            audio_paths = await asyncio.gather(*[asyncio.to_thread(task) for task in audio_download_tasks])

            for video, audio_path in zip(videos_without_subs, audio_paths):
                if audio_path:
                    video['audio_path'] = audio_path
                    downloaded_audio_files.append(audio_path)
                else:
                    video['audio_download_failed'] = True

            # Transcribe and analyze audio-based transcripts
            videos_with_audio = [v for v in videos_without_subs if v.get('audio_path')]
            print(f"\n--- Transcribing and Analyzing {len(videos_with_audio)} audio files ---")
            for video in videos_with_audio:
                video['transcript_path'] = await transcribe_audio_single(video['audio_path'], str(transcripts_dir), video.get('query_lang', 'zh'))
                if not SIMULATE_AI_PROCESSING:
                    analyze_transcript_with_gemini(video['transcript_path'], template_content, user_additional_prompt)
                else:
                    sim_path = summary_dir / f"{Path(video['transcript_path']).stem}_summary.txt"
                    with open(sim_path, 'w', encoding='utf-8') as f: f.write(f"[Simulated] Analysis for {video['title']}")

        print("\n--- Combining and Extracting Final Information ---")
        if not SIMULATE_AI_PROCESSING:
            final_summary_path = combine_and_extract_final_info(str(job_dir))
        else:
            final_summary_path = job_dir / 'final_extracted_info.txt'
            with open(final_summary_path, 'w', encoding='utf-8') as f: f.write(f"[Simulated] Final summary for {query}")

        final_content = ""
        if final_summary_path and Path(final_summary_path).is_file():
            with open(final_summary_path, 'r', encoding='utf-8') as f:
                final_content = f.read()

        individual_summaries = []
        for summary_file in summary_dir.glob('*_summary.txt'):
            video_id_match = re.match(r"([a-zA-Z0-9_-]+)", summary_file.stem)
            if video_id_match:
                video_id = video_id_match.group(1)
                # Find corresponding video info
                video_info = next((v for v in videos_to_process if v['video_id'] == video_id), None)
                if video_info:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_content = f.read()
                    
                    full_transcript_content = ""
                    if video_info.get('transcript_path') and Path(video_info['transcript_path']).is_file():
                        with open(video_info['transcript_path'], 'r', encoding='utf-8') as f_transcript:
                            full_transcript_content = f_transcript.read()

                    individual_summaries.append({
                        "title": video_info['title'],
                        "url": video_info['url'],
                        "summary": summary_content,
                        "full_transcript": full_transcript_content
                    })

        end_time = time.time()
        print(f"--- Total Execution Time: {end_time - start_time:.2f} seconds ---")

        return {
            "status": "success",
            "result": {
                "final_content": final_content,
                "individual_summaries": individual_summaries
            }
        }

    except Exception as e:
        import traceback
        print(f"An error occurred in run_analysis for job {job_id}: {e}", file=sys.stderr)
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    
    finally:
        print(f"--- Cleaning up {len(downloaded_audio_files)} audio files for job {job_id} ---")
        for audio_file in downloaded_audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    print(f"Removed audio file: {audio_file}")
            except OSError as e:
                print(f"Error removing audio file {audio_file}: {e}", file=sys.stderr)