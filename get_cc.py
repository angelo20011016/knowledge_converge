import os
import time

def delete_srt_files(folder_path: str):
    """
    遍歷指定資料夾，刪除所有 .srt 結尾的檔案。
    """
    print(f"--- 準備開始刪除資料夾中的 .srt 檔案 ---")
    print(f"目標資料夾: {folder_path}")
    
    # 檢查目標路徑是否存在
    if not os.path.isdir(folder_path):
        print(f"\n錯誤：找不到資料夾 '{folder_path}'。請檢查路徑是否正確。")
        return

    # 找到所有 .srt 檔案
    srt_files_to_delete = [f for f in os.listdir(folder_path) if f.endswith(".srt")]

    if not srt_files_to_delete:
        print("\n在目標資料夾中沒有找到任何 .srt 檔案。")
        return

    print(f"\n將會刪除以下 {len(srt_files_to_delete)} 個檔案：")
    for filename in srt_files_to_delete:
        print(f" - {filename}")

    # 提供一個最後的確認機會
    # time.sleep(2) # 暫停2秒，讓使用者有時間反應
    try:
        confirm = input("\n你確定要永久刪除這些檔案嗎？ (輸入 'yes' 來確認): ")
    except KeyboardInterrupt:
        print("\n操作已取消。")
        return
        
    if confirm.lower() == 'yes':
        print("\n開始執行刪除操作...")
        deleted_count = 0
        for filename in srt_files_to_delete:
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
                print(f"已刪除: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"刪除檔案 {filename} 時發生錯誤: {e}")
        
        print(f"\n--- 操作完成！總共刪除了 {deleted_count} 個 .srt 檔案。 ---")
    else:
        print("\n操作已取消。沒有檔案被刪除。")


# --- 主執行區塊 ---
if __name__ == '__main__':
    # ===============================================================
    #  請將這裡的路徑修改為你存放 .srt 檔案的實際資料夾路徑
    # ===============================================================
    target_folder = r"D:\projects\張修修的自由之路_subtitles"

    # 執行刪除函式
    delete_srt_files(target_folder)