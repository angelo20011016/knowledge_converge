import json
import os
import sys
import time
from pathlib import Path
from googletrans import Translator, LANGUAGES
from dotenv import load_dotenv

# --- Configuration for AI Processing ---
# Set to True to simulate AI processing without making actual API calls.
# Set to False to enable actual AI processing (requires GEMINI_API_KEY in .env).
SIMULATE_AI_PROCESSING = False

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
from transcribe_wav import transcribe_audio_single
from summarize_transcripts import analyze_transcripts
from combine_transcripts import combine_transcripts

# Import new AI processing modules
from analyze_transcript_with_gemini import analyze_transcript_with_gemini
from combine_and_extract_final_info import combine_and_extract_final_info


def translate_query(query: str) -> str:
    if all(ord(c) < 128 for c in query):
        print(f"Query '{query}' appears to be English, skipping translation.")
        return query
    try:
        translator = Translator()
        source_lang = translator.detect(query).lang
        translated = translator.translate(query, src=source_lang, dest='en')
        print(f"Translated '{query}' from {LANGUAGES.get(source_lang, 'Unknown')} to English: '{translated.text}'")
        return translated.text
    except Exception as e:
        print(f"Translation failed: {e}. Using original query.")
        return query

def step1_get_urls() -> str | None:
    chinese_query = input("請輸入您想搜尋的中文主題: ")
    safe_folder_name = "".join(c for c in chinese_query if c.isalnum() or c in (' ', '_')).rstrip()
    output_dir = os.path.join(current_dir, 'Question', safe_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    english_query = translate_query(chinese_query)
    
    all_videos = {} # Use dict for deduplication by video_id

    # Process Chinese query
    print(f"\n--- Starting search for '{chinese_query}' (Language: zh) ---")
    try:
        videos = get_videos_by_api(chinese_query, max_results=5)
        for video in videos:
            all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': 'zh'}
        print(f"Found {len(videos)} results. Total unique videos so far: {len(all_videos)}.")
    except Exception as e:
        print(f"An error occurred during YouTube API call: {e}")

    # Process English query if it's different
    if chinese_query.lower() != english_query.lower():
        print(f"\n--- Starting search for '{english_query}' (Language: en) ---")
        try:
            videos = get_videos_by_api(english_query, max_results=5)
            for video in videos:
                all_videos[video['video_id']] = {'title': video['title'], 'url': video['url'], 'query_lang': 'en'}
            print(f"Found {len(videos)} results. Total unique videos so far: {len(all_videos)}.")
        except Exception as e:
            print(f"An error occurred during YouTube API call: {e}")

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

def main():
    start_time = time.time()
    
    load_dotenv()
    if not os.environ.get("YOUTUBE_API_KEY"):
        print("Warning: 'YOUTUBE_API_KEY' environment variable is not set.")
        print("Searches using the Google API will fail.")
    
    urls_json_path = step1_get_urls()

    if not urls_json_path:
        print("No URLs to process. Exiting.")
        return

    try:
        with open(urls_json_path, 'r', encoding='utf-8') as f:
                videos_to_process = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading videos from {urls_json_path}: {e}", file=sys.stderr)
        return

    # Define common directories
    question_dir = Path(urls_json_path).parent
    subs_dir = question_dir / 'subs'
    audio_dir = question_dir / 'audio_files'
    transcripts_dir = question_dir / 'transcripts'

    os.makedirs(subs_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)

    # --- New Workflow ---

    # 1. Attempt official subtitles & clean them
    videos_for_audio_download = []
    for i, video in enumerate(videos_to_process):
        print(f"\n--- Processing video {i+1}/{len(videos_to_process)} for official subtitle ---\n")
        lang_prefs = ['en', 'en-US', 'en-GB'] if video.get('query_lang') == 'en' else ['zh-Hant', 'zh-TW', 'zh', 'zh-Hans']
        
        subtitle_path = None
        try:
            subtitle_path = get_subtitle(video['url'], output_dir=str(subs_dir), lang_prefs=lang_prefs)
            if subtitle_path:
                video['subtitle_path'] = subtitle_path
                print(f"Official subtitle downloaded for {video['title']}")
                # Clean immediately
                print(f"Cleaning official subtitle for {video['title']}")
                try:
                    cleaned_transcript_path = clean_vtt_file(subtitle_path, output_dir=str(transcripts_dir))
                    video['transcript_path'] = cleaned_transcript_path
                    print(f"已將清理後的轉錄稿儲存至：{cleaned_transcript_path}")

                    # --- AI 處理：分析單個轉錄稿 (官方 CC) ---
                    if not SIMULATE_AI_PROCESSING:
                        print(f"正在呼叫 analyze_transcript_with_gemini 處理：{cleaned_transcript_path}...")
                        analyze_transcript_with_gemini(cleaned_transcript_path)
                    else:
                        print(f"[模擬] 正在呼叫 analyze_transcript_with_gemini 處理：{cleaned_transcript_path}")
                        # 模擬資料夾建立和檔案寫入
                        simulated_video_id = Path(cleaned_transcript_path).stem
                        simulated_summary_dir = question_dir / 'summary' / simulated_video_id
                        os.makedirs(simulated_summary_dir, exist_ok=True)
                        with open(simulated_summary_dir / 'analysis.txt', 'w', encoding='utf-8') as f:
                            f.write(f"[模擬] 針對 {simulated_video_id} 的分析 (官方 CC)")
                        print(f"[模擬] 分析結果已儲存至：{simulated_summary_dir / 'analysis.txt'}")
                except Exception as e:
                    print(f"清理官方字幕時發生錯誤，影片：{video['title']}，錯誤訊息：{e}", file=sys.stderr)
                    video['transcript_failed'] = True # 標記為清理失敗
            else:
                print(f"No official subtitle found for {video['title']}. Will attempt audio download.")
                videos_for_audio_download.append(video)
        except Exception as e:
            print(f"Error getting official subtitle for {video['title']}: {e}", file=sys.stderr)
            videos_for_audio_download.append(video) # Add to list for audio download if any error occurs

    # 2. Batch audio download for videos without official subtitles
    print("\n--- Batch Audio Download for videos without official subtitles ---\n")
    audio_download_queue = []
    for i, video in enumerate(videos_for_audio_download):
        print(f"\n--- Processing video {i+1}/{len(videos_for_audio_download)} for audio download ---\n")
        try:
            audio_path = download_audio(video['url'], output_dir=str(audio_dir))
            if audio_path:
                video['audio_path'] = audio_path
                audio_download_queue.append(video)
                print(f"Audio downloaded for {video['title']}")
            else:
                video['audio_download_failed'] = True
                print(f"Audio download failed for {video['title']}")
        except Exception as e:
            video['audio_download_failed'] = True
            print(f"Error downloading audio for {video['title']}: {e}", file=sys.stderr)

    # 3. Batch STT for downloaded audio files
    print("\n--- Batch Transcription (STT) for downloaded audio files---\n")
    model_params = {"model_size_or_path": "base", "device": "cuda", "compute_type": "int8"} # Define once
    for i, video in enumerate(audio_download_queue):
        print(f"\n--- Transcribing audio for {video['title']} ({i+1}/{len(audio_download_queue)}) ---\n")
        if video.get('audio_path'):
            try:
                transcript_path = transcribe_audio_single(
                    audio_path=video['audio_path'],
                    output_dir=str(transcripts_dir),
                    model_params=model_params,
                    language=video.get('query_lang', 'zh')
                )
                if transcript_path:
                    video['transcript_path'] = transcript_path
                    print(f"轉錄完成，影片：{video['title']}")

                else:
                    video['transcription_failed'] = True
                    print(f"轉錄失敗，影片：{video['title']}")
            except Exception as e:
                video['transcription_failed'] = True
                print(f"Error transcribing audio for {video['title']}: {e}", file=sys.stderr)
        else:
            print(f"Skipping transcription for {video['title']}: No audio path found.")

    # --- AI 處理：分析單個轉錄稿 (STT 轉錄後) ---
    print("\n--- Performing AI Analysis for STT Transcripts ---")
    for i, video in enumerate(videos_to_process):
        # Check if transcript_path exists and if it's an STT transcript (not official CC)
        # A simple way to check if it's an STT transcript is if 'audio_path' exists for the video
        # and if 'transcript_path' is set, and if it hasn't been analyzed yet.
        # We can check if an analysis file already exists for this video.
        
        if video.get('transcript_path') and video.get('audio_path'): # It's an STT transcript
            transcript_path = video['transcript_path']
            video_id = Path(transcript_path).stem
            analysis_file_path = question_dir / 'summary' / f"{video_id}.txt"

            if not analysis_file_path.exists(): # Only analyze if not already analyzed
                if not SIMULATE_AI_PROCESSING:
                    print(f"正在呼叫 analyze_transcript_with_gemini 處理 (STT): {transcript_path}...")
                    analyze_transcript_with_gemini(transcript_path)
                else:
                    print(f"[模擬] 正在呼叫 analyze_transcript_with_gemini 處理 (STT): {transcript_path}")
                    # Simulate file creation for consistency
                    with open(analysis_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"[模擬] 針對 {video_id} 的分析 (音訊 STT)")
                    print(f"[模擬] 分析結果已儲存至：{analysis_file_path}")
            else:
                print(f"分析檔案已存在，跳過 (STT): {analysis_file_path}")

    # --- AI 處理：合併並提取最終資訊 ---
    # --- Consistency Check ---
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
        # You can add more detailed logging here to identify which files are missing
    else:
        print("Consistency check passed: All processed videos have corresponding analysis files.")

    if not SIMULATE_AI_PROCESSING:
        print(f"正在呼叫 combine_and_extract_final_info 處理：{question_dir}...")
        combine_and_extract_final_info(str(question_dir))
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
    print(f"\n--- Total Execution Time: {end_time - start_time:.2f} seconds ---\n")

if __name__ == "__main__":
    main()
