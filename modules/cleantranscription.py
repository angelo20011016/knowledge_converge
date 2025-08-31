import re

def clean_stt_transcript(raw_text: str) -> str:
    """
    Cleans the raw transcript text from STT (Speech-To-Text) by removing 
    timestamps and extra whitespace.
    """
    # Remove timestamps, e.g., [0.00s - 5.50s] or [12.34 - 56.78]
    # This regex is corrected from the original to be more robust.
    clean_text = re.sub(r"[\d+\.\d+s?\s*-\s*\d+\.\d+s?]", "", raw_text)

    # Remove leading/trailing whitespace and collapse multiple newlines
    clean_text = re.sub(r"[\t ]*\n[\t ]*", "\n", clean_text).strip()

    return clean_text

if __name__ == '__main__':
    # Example usage and test case
    sample_text = """
Transcription for: some_file.wav
------------------------------------
[0.00s - 5.50s] This is the first sentence.

[6.10s - 10.20s]    This is the second sentence,
 with a line break.
------------------------------------
[ 12.34 - 56.78 ] This has different spacing.
    """
    
    print("--- Original Text ---")
    print(sample_text)
    
    cleaned_text = clean_stt_transcript(sample_text)
    
    print("\n--- Cleaned Text ---")
    print(cleaned_text)