import json
import os
import sys
import time
import asyncio
from pathlib import Path
from googletrans import Translator, LANGUAGES
from dotenv import load_dotenv
from status import current_status
import yt_dlp
import re

# --- Configuration for AI Processing ---
# Set to True to simulate AI processing without making actual API calls.
# Set to False to enable actual AI processing (requires GEMINI_API_KEY in .env).
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
        detection = await translator.detect(query)
        source_lang = detection.lang
        # Force source language to Chinese for better accuracy
        translated = await translator.translate(query, src='zh-TW', dest='en')
        print(f"Translated '{query}' from {LANGUAGES.get(source_lang, 'Unknown')} to English: '{translated.text}'")
        return translated.text
    except Exception as e:
        print(f"Translation failed: {e}. Using original query.")
        return query

async def step1_get_urls(query: str, search_mode: str, search_language: str) -> str | None:
    """
    Fetches video URLs based on the search mode.
    - Divergent mode: Searches in both Chinese and English.
    - Focused mode: Searches only in the specified language.
    """
    safe_folder_name = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
    output_dir = BASE_OUTPUT_DIR / 'Question' / safe_folder_name
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

        # Process Chinese query: Let the query string's language guide the search
        print(f"\n--- Starting Divergent Search for '{query}' (Language: Auto-detect by YouTube) ---")
        try:
            # Do NOT pass the 'lang' parameter for the Chinese part.
            # The Chinese characters in the query are a strong enough signal for YouTube's search algorithm.
            videos = get_videos_by_api(query, max_results=split_results)
            for video in videos:
                all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': 'zh'}
            print(f"Found {len(videos)} results. Total unique videos so far: {len(all_videos)}.")
        except Exception as e:
            print(f"An error occurred during YouTube API call for Chinese query: {e}")

        # Process English query if it's different, and we still need more videos
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

    output_filename = os.path.join(output_dir, 'urls.json')
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(videos_to_save, f, ensure_ascii=False, indent=4)

    print(f"\nSuccessfully completed! Found {len(all_videos)} unique videos.")
    print(f"Results saved to {output_filename}")
    return output_filename

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

async def run_analysis_for_url(url: str, title: str | None = None, language: str = 'en'):
    """
    Runs the analysis pipeline for a single YouTube URL.
    Accepts an optional title; if not provided, it will be fetched from YouTube.
    Returns a dictionary with title, url, and summary content.
    """
    print(f"--- run_analysis_for_url: START for {url} with lang={language} ---")
    start_time = time.time()
    current_status["main"] = "Initializing for URL"
    current_status["sub"] = "Fetching video information..."

    video_id = None
    video_title = title # Use the provided title first
    safe_folder_name = None

    # If no title is provided, fetch it from the URL
    if not video_title:
        video_info = get_video_info_from_url(url)
        if not video_info:
            current_status["main"] = "Error"
            current_status["sub"] = "Could not fetch video info from URL."
            return {"title": "Error", "url": url, "summary": "Invalid YouTube URL or failed to fetch video info."}
        video_id = video_info["video_id"]
        video_title = video_info["title"]
        safe_folder_name = video_info["safe_folder_name"]
    else:
        # If a title is provided, we still need the video_id for file naming
        # and we create a safe folder name from the user's title
        info = get_video_info_from_url(url) # We still need the ID
        if not info:
            current_status["main"] = "Error"
            current_status["sub"] = "Could not fetch video info from URL."
            return {"title": "Error", "url": url, "summary": "Invalid YouTube URL or failed to fetch video info."}
        video_id = info["video_id"]
        safe_folder_name = "".join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()

    # Use a similar directory structure as the main analysis
    question_dir = BASE_OUTPUT_DIR / 'Single_URL' / safe_folder_name
    subs_dir = question_dir / 'subs'
    audio_dir = question_dir / 'audio_files'
    transcripts_dir = question_dir / 'transcripts'
    summary_dir = question_dir / 'summary'

    current_status["main"] = "Preparing Directories"
    current_status["sub"] = f"Creating folders for '{video_title[:30]}...'"
    os.makedirs(subs_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    transcript_path = None

    # --- Main Processing Logic (adapted from run_analysis) ---

    # 1. Try to get official subtitles
    current_status["main"] = "Processing Subtitles"
    current_status["sub"] = f"Checking for official subtitles..."
    lang_prefs = ['zh-Hant', 'zh-TW', 'zh'] if language == 'zh' else ['en', 'en-US']
    try:
        subtitle_path = get_subtitle(url, output_dir=str(subs_dir), lang_prefs=lang_prefs)
        if subtitle_path:
            print(f"Official subtitle downloaded: {subtitle_path}")
            current_status["sub"] = "Cleaning official subtitle..."
            cleaned_path = clean_vtt_file(subtitle_path, output_dir=str(transcripts_dir))
            transcript_path = cleaned_path
            print(f"Official subtitle cleaned and saved to: {transcript_path}")
        else:
            print("No suitable official subtitle found.")
            current_status["sub"] = "No official subtitle found. Proceeding to audio download."
    except Exception as e:
        print(f"An error occurred during subtitle processing: {e}", file=sys.stderr)
        current_status["sub"] = "Error fetching subtitles. Proceeding to audio download."

    # 2. If no transcript from subtitles, process audio
    if not transcript_path:
        current_status["main"] = "Downloading Audio"
        current_status["sub"] = "Downloading video audio..."
        try:
            audio_path = download_audio(url, output_dir=str(audio_dir))
            if audio_path:
                print(f"Audio downloaded successfully: {audio_path}")
                current_status["main"] = "Transcribing Audio"
                current_status["sub"] = "This may take a few minutes..."
                transcript_path = await transcribe_audio_single(
                    audio_path=audio_path,
                    output_dir=str(transcripts_dir),
                    language=language
                )
                print(f"Audio transcribed successfully: {transcript_path}")
            else:
                raise Exception("Audio download returned no path.")
        except Exception as e:
            print(f"Failed to process audio: {e}", file=sys.stderr)
            current_status["main"] = "Error"
            current_status["sub"] = "Failed to download or transcribe audio."
            return {"title": video_title, "url": url, "summary": f"Failed to process audio: {e}"}

    # 3. Analyze the final transcript (from subs or audio)
    if transcript_path:
        current_status["main"] = "Analyzing Transcript"
        current_status["sub"] = "Using AI to generate insights..."
        try:
            transcript_filename = Path(transcript_path).stem
            final_analysis_path = summary_dir / f"{transcript_filename}_summary.txt"

            if not SIMULATE_AI_PROCESSING:
                analyze_transcript_with_gemini(transcript_path)
                print(f"AI analysis complete for {transcript_path}")
            else:
                with open(final_analysis_path, 'w', encoding='utf-8') as f:
                    f.write(f"[Simulated] Analysis for {video_title}")
                print(f"Simulated AI analysis for {transcript_path}")
            
            if not final_analysis_path.is_file():
                raise FileNotFoundError(f"Could not find the generated analysis file: {final_analysis_path}")

            # Read the content of the summary file
            summary_content = ""
            with open(final_analysis_path, 'r', encoding='utf-8') as f:
                summary_content = f.read()

            end_time = time.time()
            current_status["main"] = "Completed"
            current_status["sub"] = f"Total time: {end_time - start_time:.2f}s"
            print(f"--- Total Execution Time: {end_time - start_time:.2f} seconds ---")
            
            return {
                "title": video_title,
                "url": url,
                "summary": summary_content
            }
        except Exception as e:
            print(f"An error occurred during AI analysis: {e}", file=sys.stderr)
            current_status["main"] = "Error"
            current_status["sub"] = "Failed during final AI analysis."
            return {"title": video_title, "url": url, "summary": f"AI analysis failed: {e}"}
    else:
        current_status["main"] = "Error"
        current_status["sub"] = "Could not generate a transcript."
        return {"title": video_title, "url": url, "summary": "Failed to generate a transcript from subtitles or audio."}


async def run_analysis(query: str, process_audio: bool = False, search_mode: str = 'divergent', search_language: str = 'zh'):
    """
    Main analysis pipeline for a given query.
    """
    print("--- run_analysis: START ---")
    start_time = time.time()

    current_status["main"] = "Initializing"
    current_status["sub"] = "Loading environment variables..."

    load_dotenv()
    if not os.environ.get("YOUTUBE_API_KEY"):
        print("Warning: 'YOUTUBE_API_KEY' environment variable is not set.")
        print("Searches using the Google API will fail.")

    current_status["main"] = "Fetching Video URLs"
    current_status["sub"] = f"Searching for '{query}'..."
    urls_json_path = await step1_get_urls(query, search_mode, search_language)

    if not urls_json_path:
        print("No URLs to process. Exiting.")
        current_status["main"] = "Finished"
        current_status["sub"] = "No videos found."
        return

    current_status["main"] = "Loading Video List"
    current_status["sub"] = f"Loading videos from {urls_json_path}..."
    try:
        with open(urls_json_path, 'r', encoding='utf-8') as f:
                videos_to_process = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading videos from {urls_json_path}: {e}", file=sys.stderr)
        current_status["main"] = "Error"
        current_status["sub"] = f"Failed to load video list: {e}"
        return

    # Define common directories
    question_dir = Path(urls_json_path).parent
    subs_dir = question_dir / 'subs'
    audio_dir = question_dir / 'audio_files'
    transcripts_dir = question_dir / 'transcripts'

    current_status["main"] = "Preparing Directories"
    current_status["sub"] = "Creating necessary folders..."
    os.makedirs(subs_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)

    # --- New Workflow ---

    # 1. Attempt official subtitles & clean them
    videos_for_audio_download = []
    current_status["main"] = "Processing Subtitles"
    for i, video in enumerate(videos_to_process):
        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Checking official subtitles..."
        print(f"\n--- Processing video {i+1}/{len(videos_to_process)} for official subtitle ---\n")
        lang_prefs = ['en', 'en-US', 'en-GB'] if video.get('query_lang') == 'en' else ['zh-Hant', 'zh-TW', 'zh', 'zh-Hans']

        subtitle_path = None
        try:
            subtitle_path = get_subtitle(video['url'], output_dir=str(subs_dir), lang_prefs=lang_prefs)
            if subtitle_path:
                video['subtitle_path'] = subtitle_path
                current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Official subtitle downloaded."
                print(f"Official subtitle downloaded for {video['title']}")
                # Clean immediately
                current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Cleaning official subtitle..."
                print(f"Cleaning official subtitle for {video['title']}")
                try:
                    cleaned_transcript_path = clean_vtt_file(subtitle_path, output_dir=str(transcripts_dir))
                    video['transcript_path'] = cleaned_transcript_path
                    current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Transcript saved."
                    print(f"已將清理後的轉錄稿儲存至：{cleaned_transcript_path}")

                    # --- AI 處理：分析單個轉錄稿 (官方 CC) ---
                    if not SIMULATE_AI_PROCESSING:
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Analyzing official transcript (AI)..."
                        print(f"--- Before analyze_transcript_with_gemini (Official CC) for {video['title']} ---")
                        analyze_transcript_with_gemini(cleaned_transcript_path)
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Official transcript analyzed."
                        print(f"--- After analyze_transcript_with_gemini (Official CC) for {video['title']} ---")
                    else:
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Simulating official transcript analysis."
                        print(f"[模擬] 正在呼叫 analyze_transcript_with_gemini 處理：{cleaned_transcript_path}")
                        # 模擬資料夾建立和檔案寫入
                        simulated_video_id = Path(cleaned_transcript_path).stem
                        simulated_summary_dir = question_dir / 'summary' / simulated_video_id
                        os.makedirs(simulated_summary_dir, exist_ok=True)
                        with open(simulated_summary_dir / 'analysis.txt', 'w', encoding='utf-8') as f:
                            f.write(f"[模擬] 針對 {simulated_video_id} 的分析 (官方 CC)")
                        print(f"[模擬] 分析結果已儲存至：{simulated_summary_dir / 'analysis.txt'}")
                except Exception as e:
                    current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Error cleaning/analyzing official subtitle."
                    print(f"清理官方字幕時發生錯誤，影片：{video['title']}，錯誤訊息：{e}", file=sys.stderr)
                    video['transcript_failed'] = True # 標記為清理失敗
            else:
                current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - No official subtitle found."
                if process_audio:
                    print(f"No official subtitle found for {video['title']}. Will attempt audio download.")
                    videos_for_audio_download.append(video)
                else:
                    print(f"No official subtitle found for {video['title']}. Skipping audio processing as per settings.")
        except Exception as e:
            current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Error getting official subtitle."
            print(f"Error getting official subtitle for {video['title']}: {e}", file=sys.stderr)
            if process_audio:
                videos_for_audio_download.append(video) # Add to list for audio download if any error occurs

    if process_audio:
        # 2. Batch audio download for videos without official subtitles
        current_status["main"] = "Downloading Audio"
        print("\n--- Batch Audio Download for videos without official subtitles ---\n")
        audio_download_queue = []
        for i, video in enumerate(videos_for_audio_download):
            current_status["sub"] = f"Video {i+1}/{len(videos_for_audio_download)}: {video['title']} - Downloading audio..."
            print(f"\n--- Processing video {i+1}/{len(videos_for_audio_download)} for audio download ---\n")
            try:
                audio_path = download_audio(video['url'], output_dir=str(audio_dir))
                if audio_path:
                    video['audio_path'] = audio_path
                    audio_download_queue.append(video)
                    current_status["sub"] = f"Video {i+1}/{len(videos_for_audio_download)}: {video['title']} - Audio downloaded."
                    print(f"Audio downloaded for {video['title']}")
                else:
                    video['audio_download_failed'] = True
                    current_status["sub"] = f"Video {i+1}/{len(videos_for_audio_download)}: {video['title']} - Audio download failed."
                    print(f"Audio download failed for {video['title']}")
            except Exception as e:
                video['audio_download_failed'] = True
                current_status["sub"] = f"Video {i+1}/{len(videos_for_audio_download)}: {video['title']} - Error downloading audio."
                print(f"Error downloading audio for {video['title']}: {e}", file=sys.stderr)

        # 3. Batch STT for downloaded audio files using asyncio for parallelism
        current_status["main"] = "Transcribing Audio (Parallel)"
        print("\n--- Batch Transcription (STT) for downloaded audio files---\n")
        
        transcription_tasks = []
        for video in audio_download_queue:
            if video.get('audio_path'):
                task = transcribe_audio_single(
                    audio_path=video['audio_path'],
                    output_dir=str(transcripts_dir),
                    language=video.get('query_lang', 'zh')
                )
                transcription_tasks.append(task)
            else:
                current_status["sub"] = f"Skipping transcription for {video['title']} (no audio)."
                print(f"Skipping transcription for {video['title']}: No audio path found.")

        if transcription_tasks:
            current_status["sub"] = f"Transcribing {len(transcription_tasks)} audio files in parallel..."
            # Run all transcription tasks concurrently
            transcript_paths = await asyncio.gather(*transcription_tasks)

            # Associate the returned paths with their videos
            for i, video in enumerate(audio_download_queue):
                if transcript_paths[i]:
                    video['transcript_path'] = transcript_paths[i]
                    current_status["sub"] = f"Transcription complete for: {video['title']}"
                    print(f"Transcription successful for: {video['title']}")
                else:
                    video['transcription_failed'] = True
                    current_status["sub"] = f"Transcription failed for: {video['title']}"
                    print(f"Transcription failed for: {video['title']}")
        
        # Short delay to allow disk I/O to settle before AI analysis
        time.sleep(2)

        # --- AI 處理：分析單個轉錄稿 (STT 轉錄後) ---
        current_status["main"] = "Analyzing STT Transcripts"
        print("\n--- Performing AI Analysis for STT Transcripts ---")
        for i, video in enumerate(videos_to_process):
            if video.get('transcript_path') and video.get('audio_path'): # It's an STT transcript
                transcript_path = video['transcript_path']
                video_id = Path(transcript_path).stem
                analysis_file_path = question_dir / 'summary' / f"{video_id}.txt"

                if not analysis_file_path.exists(): # Only analyze if not already analyzed
                    if not SIMULATE_AI_PROCESSING:
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Analyzing STT transcript (AI)..."
                        print(f"--- Before analyze_transcript_with_gemini (STT) for {video['title']} ---")
                        analyze_transcript_with_gemini(transcript_path)
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - STT transcript analyzed."
                        print(f"--- After analyze_transcript_with_gemini (STT) for {video['title']} ---")
                    else:
                        current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Simulating STT transcript analysis."
                        print(f"[模擬] 正在呼叫 analyze_transcript_with_gemini 處理 (STT): {transcript_path}")
                        # 模擬資料夾建立和檔案寫入
                        with open(analysis_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"[模擬] 針對 {video_id} 的分析 (音訊 STT)")
                        print(f"[模擬] 分析結果已儲存至：{analysis_file_path}")
                else:
                    current_status["sub"] = f"Video {i+1}/{len(videos_to_process)}: {video['title']} - Analysis file already exists (STT)."
                    print(f"分析檔案已存在，跳過 (STT): {analysis_file_path}")

    # --- AI 處理：合併並提取最終資訊 ---
    # --- Consistency Check ---
    current_status["main"] = "Performing Consistency Check"
    current_status["sub"] = "Verifying processed files..."
    print("\n--- Performing Consistency Check ---")
    processed_video_count = 0
    for video in videos_to_process:
        if video.get('transcript_path') and Path(video['transcript_path']).is_file():
            processed_video_count += 1
        else:
            print(f"Warning: Video '{video.get('title', video['video_id'])}' did not produce a valid transcript.")

    summary_dir = question_dir / 'summary'
    analysis_files = list(summary_dir.glob('*.txt'))
    analysis_file_count = len(analysis_files)

    print(f"Total videos processed with transcripts: {processed_video_count}")
    print(f"Total individual AI analysis files found: {analysis_file_count}")

    if processed_video_count != analysis_file_count:
        print("WARNING: Mismatch between processed videos and analysis files!")
        current_status["sub"] = "WARNING: Mismatch in processed files!"
        # You can add more detailed logging here to identify which files are missing
    else:
        print("Consistency check passed: All processed videos have corresponding analysis files.")
        current_status["sub"] = "Consistency check passed."

    current_status["main"] = "Extracting Final Information"
    if not SIMULATE_AI_PROCESSING:
        print(f"--- Before combine_and_extract_final_info ---")
        combine_and_extract_final_info(str(question_dir))
        print(f"--- After combine_and_extract_final_info ---")
    else:
        print(f"[模擬] 正在呼叫 combine_and_extract_final_info 處理：{question_dir}")
        # 模擬最終提取檔案寫入
        simulated_final_extraction_path = question_dir / 'final_extracted_info.txt'
        with open(simulated_final_extraction_path, 'w', encoding='utf-8') as f:
            f.write(f"[模擬] 針對 {question_dir.name} 的最終提取資訊")
        print(f"[模擬] 最終提取資訊已儲存至：{simulated_final_extraction_path}")

    # 4. Final check and analysis
    #step4_verify_and_analyze(videos_to_process, urls_json_path)

    end_time = time.time()
    current_status["main"] = "Completed"
    current_status["sub"] = f"Total time: {end_time - start_time:.2f}s"
    print(f"\n--- Total Execution Time: {end_time - start_time:.2f} seconds ---\n")
    print("--- run_analysis: END ---")

    # Collect and return results
    final_extracted_info_path = question_dir / 'final_extracted_info.txt'
    
    # Create a structured list of individual summaries with all necessary info
    individual_summaries_data = []
    video_info_map = {v['video_id']: v for v in videos_to_process}
    summary_files = (question_dir / 'summary').glob('*_summary.txt')

    for summary_file in summary_files:
        # Extract video_id from filename like 'VIDEOID_transcript_summary.txt'
        video_id = summary_file.stem.split('_')[0]
        if video_id in video_info_map:
            video_info = video_info_map[video_id]
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                individual_summaries_data.append({
                    "title": video_info['title'],
                    "url": video_info['url'],
                    "summary": content
                })
            except Exception as e:
                print(f"Error reading summary file {summary_file}: {e}", file=sys.stderr)

    return {
        "final_extracted_info_path": str(final_extracted_info_path),
        "individual_summaries_data": individual_summaries_data
    }
