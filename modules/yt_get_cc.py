from yt_dlp import YoutubeDL, utils
from pathlib import Path
import sys
import os
import re
import time

def _sanitize_filename(name: str) -> str:
    """Helper to replace unsafe characters in a filename with underscores."""
    return re.sub(r'[^\w\d.-]+', '_', name)

def get_subtitle(url: str, output_dir: str, lang_prefs: list[str] = None) -> str | None:
    """
    Finds and downloads a subtitle based on language preferences.
    It first tries to find a subtitle from the preferred languages list.
    If none are found, it downloads the first available subtitle in any language.
    Includes a retry mechanism.

    Returns:
        The path to the downloaded VTT file, or None if no subtitles are found at all.
    """
    if lang_prefs is None:
        lang_prefs = ['zh-Hant', 'zh-TW', 'zh', 'zh-Hans']

    info = None
    # Try to get video info, with one retry on failure.
    for attempt in range(2):
        try:
            with YoutubeDL({"skip_download": True, "quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            break  # Success
        except Exception as e:
            print(f"Attempt {attempt + 1} to fetch subtitle info failed: {e}", file=sys.stderr)
            if attempt == 0:
                print("Retrying in 5 seconds...")
                time.sleep(5)
    
    if not info:
        print(f"Could not fetch subtitle info for {url} after all attempts.", file=sys.stderr)
        return None

    # --- Find best available language ---
    subtitles = info.get("subtitles", {}) or {}
    auto_captions = info.get("automatic_captions", {}) or {}
    
    # Filter out live chat subtitles
    available_subs = {}
    for lang, subs_list in subtitles.items():
        # Check if any of the subtitle formats for this language are NOT live chat
        if any(not (sub.get('ext') == 'json' or 'live_chat' in sub.get('protocol', '')) for sub in subs_list):
            available_subs[lang] = subs_list
            
    available_auto_captions = {}
    for lang, subs_list in auto_captions.items(): # Corrected indentation here
        # Check if any of the automatic caption formats for this language are NOT live chat
        if any(not (sub.get('ext') == 'json' or 'live_chat' in sub.get('protocol', '')) for sub in subs_list):
            available_auto_captions[lang] = subs_list

    all_subs_langs = list(available_subs.keys()) + list(available_auto_captions.keys())
    title = info.get('title', 'video')
    target_lang = None

    for lang in lang_prefs:
        if lang in all_subs_langs:
            target_lang = lang
            print(f"Found preferred subtitle language: {target_lang}")
            break
    
    if not target_lang and all_subs_langs:
        target_lang = all_subs_langs[0]
        print(f"No preferred subtitle found. Falling back to first available: {target_lang}")

    if not target_lang:
        print(f"No subtitles found for {url}")
        return None

    # --- Download the specific subtitle ---
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    safe_title = _sanitize_filename(title)
    video_id = info.get('id', safe_title) # Use video_id for filename, fallback to title
    is_auto_sub = target_lang in auto_captions and target_lang not in subtitles

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": not is_auto_sub,
        "writeautomaticsub": is_auto_sub,
        "subtitleslangs": [target_lang],
        "subtitlesformat": "vtt",
        "outtmpl": str(output_path / f"{video_id}.%(language)s"), # Use video_id for filename
        "quiet": True,
        "no_warnings": True,
    }

    downloaded_filepath = None
    for attempt in range(2):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                download_info = ydl.extract_info(url, download=True)
                
                # Get the exact path from yt-dlp's output info
                requested_subs = download_info.get('requested_subtitles')
                if requested_subs and target_lang in requested_subs:
                    sub_info = requested_subs[target_lang]
                    # 'filepath' key is available in newer yt-dlp versions and is most reliable
                    if 'filepath' in sub_info:
                        downloaded_filepath = sub_info['filepath']
                    else: # Fallback for older versions or different structures
                        ext = sub_info.get('ext')
                        if ext:
                            base_path = ydl_opts['outtmpl']
                            final_path = f"{base_path}.{ext}"
                            if os.path.exists(final_path):
                                downloaded_filepath = final_path

            if downloaded_filepath and os.path.exists(downloaded_filepath):
                print(f"Subtitle downloaded to: {downloaded_filepath}")
                return downloaded_filepath
            else:
                print(f"Info: Subtitle for lang '{target_lang}' not available or empty for {video_id}. Proceeding without it.")
                return None

        except utils.DownloadError as e:
            print(f"Warning: yt-dlp failed to download subtitle for {video_id}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Attempt {attempt + 1} to download subtitle failed with unexpected error: {e}", file=sys.stderr)
            if attempt == 0:
                print("Retrying in 5 seconds...")
                time.sleep(5)