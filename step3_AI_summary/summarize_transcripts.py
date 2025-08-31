from pathlib import Path
import os

def analyze_transcripts(transcript_paths: list[str]):
    """
    Analyzes a list of transcript files to count words and estimate tokens.

    Args:
        transcript_paths: A list of absolute paths to the transcript .txt files.
    """
    print("\n--- Starting Step 3: Analyzing Transcripts ---")
    
    if not transcript_paths:
        print("No transcript files provided to analyze.")
        return

    total_word_count = 0
    
    for file_path_str in transcript_paths:
        try:
            file_path = Path(file_path_str)
            if not file_path.is_file():
                print(f"Warning: File not found at {file_path_str}. Skipping.")
                continue

            text = file_path.read_text(encoding='utf-8').strip()
            
            # Calculate word count as a proxy for token count
            word_count = len(text.split())
            
            print(f"  - Analysis for: {file_path.name}")
            print(f"    - Word Count (Token Estimate): {word_count}")
            
            total_word_count += word_count

        except Exception as e:
            print(f"Error analyzing file {file_path_str}: {e}")

    print("\n--- Analysis Summary ---")
    print(f"Total files analyzed: {len(transcript_paths)}")
    print(f"Total Word Count (Token Estimate) for all files: {total_word_count}")
    print("--- Finished Step 3 ---")

if __name__ == '__main__':
    # Example usage for standalone testing
    # Create a dummy directory and some dummy files
    print("--- Running standalone test for summarize_transcripts.py ---")
    dummy_dir = Path("dummy_transcripts_for_test")
    dummy_dir.mkdir(exist_ok=True)
    
    dummy_file_1 = dummy_dir / "test1.txt"
    dummy_file_1.write_text("This is a test file with seven words.", encoding="utf-8")
    
    dummy_file_2 = dummy_dir / "test2.txt"
    dummy_file_2.write_text("This is another test file, it has ten words in total.", encoding="utf-8")
    
    dummy_paths = [str(dummy_file_1.resolve()), str(dummy_file_2.resolve())]
    
    analyze_transcripts(dummy_paths)
    
    # Clean up dummy files
    os.remove(dummy_file_1)
    os.remove(dummy_file_2)
    os.rmdir(dummy_dir)
