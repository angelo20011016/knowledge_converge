from pathlib import Path
import math

def combine_transcripts(transcript_paths: list[str], output_dir: str, max_tokens_per_file: int = 100000) -> list[str]:
    """
    Combines multiple transcript files into one or more files based on a token limit.

    Args:
        transcript_paths: A list of absolute paths to the transcript .txt files.
        output_dir: The directory where the combined/split files will be saved.
        max_tokens_per_file: The maximum number of words (as a proxy for tokens) per output file.

    Returns:
        A list of paths to the newly created combined/split files.
    """
    print("\n--- Starting Step 3: Combining Transcripts ---")
    
    if not transcript_paths:
        print("No transcript files provided for combining.")
        return []

    all_content = []
    total_word_count = 0

    # Read all content and count words
    for file_path_str in transcript_paths:
        try:
            file_path = Path(file_path_str)
            if not file_path.is_file():
                print(f"Warning: File not found at {file_path_str}. Skipping.")
                continue

            content = file_path.read_text(encoding='utf-8').strip()
            word_count = len(content.split())
            all_content.append({'content': content, 'word_count': word_count, 'name': file_path.name})
            total_word_count += word_count
        except Exception as e:
            print(f"Error reading file {file_path_str} for combining: {e}")

    if not all_content:
        print("No valid content found to combine.")
        return []

    output_files = []
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if total_word_count <= max_tokens_per_file:
        # Combine all into one file
        combined_text = "\n\n".join([item['content'] for item in all_content])
        output_filename = output_dir_path / "combined_transcript_part_1.txt"
        output_filename.write_text(combined_text, encoding='utf-8')
        output_files.append(str(output_filename))
        print(f"All transcripts combined into one file: {output_filename} (Total words: {total_word_count})")
    else:
        # Split into multiple files
        part_num = 1
        current_part_content = []
        current_part_word_count = 0

        for item in all_content:
            if current_part_word_count + item['word_count'] > max_tokens_per_file and current_part_content:
                # Save current part and start a new one
                combined_text = "\n\n".join(current_part_content)
                output_filename = output_dir_path / f"combined_transcript_part_{part_num}.txt"
                output_filename.write_text(combined_text, encoding='utf-8')
                output_files.append(str(output_filename))
                print(f"Part {part_num} saved: {output_filename} (Words: {current_part_word_count})")

                part_num += 1
                current_part_content = []
                current_part_word_count = 0
            
            current_part_content.append(item['content'])
            current_part_word_count += item['word_count']
        
        # Save the last part
        if current_part_content:
            combined_text = "\n\n".join(current_part_content)
            output_filename = output_dir_path / f"combined_transcript_part_{part_num}.txt"
            output_filename.write_text(combined_text, encoding='utf-8')
            output_files.append(str(output_filename))
            print(f"Part {part_num} saved: {output_filename} (Words: {current_part_word_count})")

    print("--- Finished Step 3: Combining Transcripts ---")
    return output_files

if __name__ == '__main__':
    # Example usage for standalone testing
    print("--- Running standalone test for combine_transcripts.py ---")
    dummy_output_dir = Path("combined_test_output")
    dummy_output_dir.mkdir(exist_ok=True)

    # Create some dummy transcript files
    dummy_transcripts = []
    for i in range(5):
        file_path = dummy_output_dir / f"dummy_transcript_{i+1}.txt"
        content = f"This is dummy content for file {i+1}. " * 1000 # 1000 words
        file_path.write_text(content, encoding="utf-8")
        dummy_transcripts.append(str(file_path))

    # Test combining (total 5000 words, should be one file)
    print("\nTest Case 1: Combining all into one file (total words < max_tokens_per_file)")
    combined_files_1 = combine_transcripts(dummy_transcripts, str(dummy_output_dir / "test1"), max_tokens_per_file=10000)
    print(f"Combined files: {combined_files_1}")

    # Test splitting (total 5000 words, should be 3 files if max_tokens_per_file=2000)
    print("\nTest Case 2: Splitting into multiple files (total words > max_tokens_per_file)")
    combined_files_2 = combine_transcripts(dummy_transcripts, str(dummy_output_dir / "test2"), max_tokens_per_file=2000)
    print(f"Combined files: {combined_files_2}")

    # Clean up dummy files and directories
    import shutil
    shutil.rmtree(dummy_output_dir)
    print("Cleaned up dummy test files.")
