import re
from pathlib import Path

def _clean_vtt_content(vtt_content: str) -> str:
    """
    Cleans a VTT (Web Video Text Tracks) content string into plain text.
    It removes VTT headers, timestamps, style information, and tags,
    and joins lines that belong to the same caption segment.
    """
    lines = vtt_content.strip().splitlines()
    cleaned_lines = []
    
    # Find the start of the actual captions (skip header)
    start_index = 0
    for i, line in enumerate(lines):
        if "-->" in line:
            start_index = i + 1
            break
    
    if start_index == 0: # No captions found
        return ""

    # Process caption lines
    text_buffer = []
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        
        # Timestamp lines indicate the end of a caption block
        if "-->" in line:
            if text_buffer:
                cleaned_lines.append(" ".join(text_buffer))
                text_buffer = []
            continue
        
        # Skip empty lines between caption blocks
        if not line:
            continue

        # Remove VTT tags and collect text
        cleaned_line = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned_line:
            text_buffer.append(cleaned_line)

    # Add the last buffered text
    if text_buffer:
        cleaned_lines.append(" ".join(text_buffer))
        
    # Remove duplicate lines while preserving order
    seen = set()
    unique_lines = [x for x in cleaned_lines if not (x in seen or seen.add(x))]

    return "\n".join(unique_lines)


def clean_vtt_file(vtt_file_path: str, output_dir: str) -> str | None:
    """
    Reads a VTT file, cleans its content, and saves it to a new text file.

    Args:
        vtt_file_path: The absolute path to the input .vtt file.
        output_dir: The directory where the cleaned .txt file will be saved.

    Returns:
        The path to the cleaned text file, or None if an error occurs.
    """
    try:
        input_path = Path(vtt_file_path)
        output_path = Path(output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        vtt_content = input_path.read_text(encoding='utf-8')
        
        cleaned_text = _clean_vtt_content(vtt_content)
        
        # Create a new filename
        output_filename = input_path.stem + "_cleaned.txt"
        output_file_path = output_path / output_filename
        
        output_file_path.write_text(cleaned_text, encoding='utf-8')
        
        print(f"Cleaned subtitle saved to: {output_file_path}")
        return str(output_file_path)

    except FileNotFoundError:
        print(f"Error: Input file not found at {vtt_file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':
    # Create a dummy VTT file for testing
    dummy_vtt_content = """WEBVTT
KIND: captions
LANGUAGE: en

00:00:01.000 --> 00:00:04.000
<v Roger>Hello world.
This is a test.

00:00:05.000 --> 00:00:09.500 align:start
This is a
multiline caption.

00:00:09.500 --> 00:00:10.500
This is a test.

00:00:11.000 --> 00:00:12.000
Another caption.
"""
    dummy_vtt_path = Path("dummy_test.vtt")
    dummy_vtt_path.write_text(dummy_vtt_content, encoding="utf-8")

    print(f"--- Testing with dummy file: {dummy_vtt_path} ---")
    
    # Test the main function
    cleaned_file = clean_vtt_file(str(dummy_vtt_path), output_dir="temp_cleaned")
    
    if cleaned_file:
        print(f"\n--- Cleaned File Content ---")
        cleaned_content = Path(cleaned_file).read_text(encoding='utf-8')
        print(cleaned_content)
        
        # Clean up the created files and directory
        import os
        os.remove(dummy_vtt_path)
        os.remove(cleaned_file)
        try:
            os.rmdir("temp_cleaned")
            print("\nSuccessfully cleaned up temporary files.")
        except OSError as e:
            print(f"Error during cleanup: {e}")
