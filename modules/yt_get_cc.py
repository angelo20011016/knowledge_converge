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
    is_auto_sub = target_lang in auto_captions and target_lang not in subtitles

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": not is_auto_sub,
        "writeautomaticsub": is_auto_sub,
        "subtitleslangs": [target_lang],
        "subtitlesformat": "vtt", # Still prefer VTT
        "outtmpl": str(output_path / f"{safe_title}.%(language)s"),
        "quiet": True,
        "no_warnings": True,
    }

    downloaded_filepath = None
    for attempt in range(2):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                # This will return the info_dict, which contains 'filepath' after download
                download_info = ydl.extract_info(url, download=True)
                downloaded_filepath = download_info.get('filepath')
            
            if downloaded_filepath and os.path.exists(downloaded_filepath):
                print(f"Subtitle downloaded to: {downloaded_filepath}")
                return downloaded_filepath
            else:
                # If filepath is not directly available or doesn't exist, try to find it by globbing
                found_files = list(output_path.glob(f"{safe_title}*"))
                if found_files:
                    # Prioritize .vtt, then .json, then any other
                    for f in found_files:
                        if f.suffix == '.vtt':
                            print(f"Found .vtt subtitle: {f}")
                            return str(f)
                    for f in found_files:
                        if f.suffix == '.json': # Live chat often downloads as JSON
                            print(f"Found .json subtitle: {f}")
                            # After filtering, this should ideally not happen for valid subtitles.
                            # But if it does, we should treat it as a failure.
                            print(f"Warning: Downloaded a .json file for {safe_title}. Treating as no valid subtitle.", file=sys.stderr)
                            os.remove(f) # Clean up the unwanted file
                            return None
                    print(f"Found other subtitle file: {found_files[0]}")
                    return str(found_files[0]) # Return the first one found
                
                print(f"Error: Subtitle file was expected but not found for {safe_title} after download.", file=sys.stderr)
                return None # Failed to find after download

        except Exception as e:
            print(f"Attempt {attempt + 1} to download subtitle failed: {e}", file=sys.stderr)
            if attempt == 0:
                print("Retrying in 5 seconds...")
                time.sleep(5)
    
    print(f"Failed to download subtitle for lang '{target_lang}' after all attempts.", file=sys.stderr)
    return None