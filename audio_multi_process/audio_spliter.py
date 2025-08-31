import librosa
import soundfile as sf
from pathlib import Path
import time
import os

def split_audio_file(audio_path: str, output_dir: str, chunk_duration_sec: float, target_sr: int, temp_subdir: str = "temp_audio_chunks") -> list[str]:
    """
    將一個音訊檔案分割成多個小檔案。

    Args:
        audio_path (str): 要分割的音訊檔案路徑。
        output_dir (str): 存放分割後音訊片段的目錄。
        chunk_duration_sec (float): 每個音訊片段的預期持續時間（秒）。
        target_sr (int): 音訊目標採樣率。
        temp_subdir (str): 在 output_dir 下創建的臨時子目錄名稱。

    Returns:
        list[str]: 所有分割後音訊檔案的路徑列表。
    """
    print(f"--- Audio Splitting Module ---")
    print(f"Splitting: {audio_path}")
    print(f"Chunk duration: {chunk_duration_sec}s, Target SR: {target_sr}")

    chunk_files = []
    try:
        # 確保輸出目錄和臨時子目錄存在
        output_path_obj = Path(output_dir)
        output_path_obj.mkdir(parents=True, exist_ok=True)
        temp_dir_path = output_path_obj / temp_subdir
        temp_dir_path.mkdir(parents=True, exist_ok=True)

        # 載入音訊
        start_load_time = time.time()
        audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
        end_load_time = time.time()
        print(f"  Loaded audio in {end_load_time - start_load_time:.2f}s. Shape: {audio.shape}, SR: {sr}")

        # 計算每個音訊塊應該包含的樣本數
        chunk_samples = int(chunk_duration_sec * sr)
        num_audio_samples = len(audio)

        if num_audio_samples == 0:
            print("  Audio file is empty.")
            return []

        base_filename = Path(audio_path).stem
        split_count = 0

        # 遍歷音訊，將其分割成塊
        for i in range(0, num_audio_samples, chunk_samples):
            chunk_start_sample = i
            chunk_end_sample = min(i + chunk_samples, num_audio_samples)
            audio_chunk = audio[chunk_start_sample:chunk_end_sample]

            if len(audio_chunk) == 0:
                continue

            # 創建音訊塊的檔案名
            chunk_filename = f"{base_filename}_part_{split_count}.wav"
            chunk_filepath = temp_dir_path / chunk_filename

            # 使用 soundfile 寫入音訊塊
            start_write_time = time.time()
            sf.write(str(chunk_filepath), audio_chunk, sr)
            end_write_time = time.time()
            print(f"  Saved chunk: {chunk_filepath} in {end_write_time - start_write_time:.2f}s")

            chunk_files.append(str(chunk_filepath))
            split_count += 1

        print(f"Successfully split {audio_path} into {len(chunk_files)} chunks.")
        return chunk_files

    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_path}")
        return []
    except Exception as e:
        print(f"An error occurred during audio splitting: {e}")
        return []

# --- 範例使用 ---
if __name__ == "__main__":
    # 測試單個檔案的分解
    test_audio_file = r"D:\projects\loacl_STT\audio_files\一期视频看懂人形机器人_下一个万亿赛道_专访安克创新CEO阳萌_大咖谈芯第15期.wav"
    output_base_dir = r"D:\projects\loacl_STT\Video_Knowledge_Convergence\audio_multi_process\processed_audio" # 存放分割後的音訊塊
    chunk_length_seconds = 30.0 # 設置分塊長度
    sample_rate = 16000

    print(f"Starting audio splitting for: {test_audio_file}")
    start_split_time = time.time()
    
    # 調用分割函數
    created_chunks = split_audio_file(
        audio_path=test_audio_file,
        output_dir=output_base_dir,
        chunk_duration_sec=chunk_length_seconds,
        target_sr=sample_rate
    )
    
    end_split_time = time.time()
    print(f"Audio splitting process finished in {end_split_time - start_split_time:.2f}s.")
    print(f"Created {len(created_chunks)} audio chunks in '{output_base_dir}/temp_audio_chunks/'.")
    
    # 打印創建的音訊塊列表
    # for chunk in created_chunks:
    #     print(f" - {chunk}")

    # 之後，您可以在另一個腳本或同一腳本的下一部分使用這些 created_chunks 進行轉錄