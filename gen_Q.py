import os
import json
import time
import google.generativeai as genai
from tqdm import tqdm

# --- 1. 設定區 ---

# 請將 'YOUR_API_KEY' 換成你的 Google AI Studio API 金鑰
GOOGLE_API_KEY = 'AIzaSyADhGthozeeeu22ojEhO0fWsJ0KmZ6TyV4'

# Markdown 檔案所在的資料夾路徑
TARGET_DIRECTORY = r'D:\projects\張修修的自由之路_subtitles'

# 要使用的模型名稱
MODEL_NAME = 'gemini-2.5-flash-lite'

# 每個批次處理的檔案數量
BATCH_SIZE = 5

# 最終輸出的 JSON 檔案名稱
OUTPUT_FILE = 'question.json'

# --- 2. 設定 API ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"API 金鑰設定失敗，請檢查你的金鑰是否正確。錯誤：{e}")
    exit()

# --- 3. 主要邏輯 ---

def generate_qa_for_text(text_content, retries=3, delay=5):
    """
    呼叫 Gemini API 為指定的文字內容生成問答對。

    Args:
        text_content (str): 合併後的 Markdown 文字內容。
        retries (int): 失敗時的重試次數。
        delay (int): 每次重試前的延遲秒數。

    Returns:
        list: 一個包含問答對字典的列表，例如 [{'question': '...', 'answer': '...'}, ...]。
              如果失敗則返回空列表。
    """
    # 設定模型和生成指令
    model = genai.GenerativeModel(MODEL_NAME)
    
    # 設計一個強大的 Prompt，引導模型產出我們想要的格式
    prompt = f"""
    你是一位專業的資料分析師，你的任務是為 RAG (Retrieval-Augmented Generation) 系統建立高品質的評估問答集。

    請仔細閱讀以下合併的多個文件內容，這些內容是影片的逐字稿。

    你的目標是根據這些內容，生成一系列精確且有深度的「問題」與「答案」。

    請遵守以下規則：
    1.  問題應該是使用者可能會真實提出的問題。
    2.  答案必須能「直接且完整地」從提供的文字中找到，不可自行演繹或總結。
    3.  每個問題都必須對應一個明確的答案。
    4.  針對這份文件，請生成 10 組問答對。
    5.  你的最終輸出「必須」是一個格式正確的 JSON 陣列 (Array)，其中每個物件 (Object) 包含 "question" 和 "answer" 兩個鍵 (key)。
    6.  除了這個 JSON 陣列之外，不要包含任何其他文字、解釋、或程式碼區塊標記 (例如 ```json ... ```)。

    這是文件內容：
    ---
    {text_content}
    ---

    請開始生成 JSON 格式的問答集：
    """

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            
            # 清理模型可能回傳的 markdown 程式碼標記
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            
            # 解析 JSON
            qa_pairs = json.loads(cleaned_response)
            
            # 驗證格式是否為 list of dicts with correct keys
            if isinstance(qa_pairs, list) and all(isinstance(p, dict) and 'question' in p and 'answer' in p for p in qa_pairs):
                return qa_pairs
            else:
                print("警告：API 回應格式不正確，將進行重試。")

        except json.JSONDecodeError:
            print(f"警告：無法解析 API 回應為 JSON，內容為：\n{response.text}\n正在重試 ({attempt + 1}/{retries})...")
        except Exception as e:
            print(f"呼叫 API 時發生錯誤：{e}。正在重試 ({attempt + 1}/{retries})...")
        
        time.sleep(delay)
        
    print("錯誤：多次重試後仍無法成功生成問答集。")
    return []


def main():
    """
    主執行函數
    """
    print(f"從資料夾 '{TARGET_DIRECTORY}' 讀取 .md 檔案...")
    
    # 檢查路徑是否存在
    if not os.path.isdir(TARGET_DIRECTORY):
        print(f"錯誤：找不到資料夾 '{TARGET_DIRECTORY}'。請檢查路徑是否正確。")
        return

    # 1. 找到所有 .md 檔案
    md_files = [f for f in os.listdir(TARGET_DIRECTORY) if f.endswith('.md')]
    if not md_files:
        print("錯誤：在資料夾中找不到任何 .md 檔案。")
        return
        
    print(f"找到 {len(md_files)} 個 .md 檔案。")

    # 2. 將檔案路徑分批
    file_batches = [md_files[i:i + BATCH_SIZE] for i in range(0, len(md_files), BATCH_SIZE)]
    print(f"已將檔案分為 {len(file_batches)} 個批次，每批 {BATCH_SIZE} 個檔案。")

    all_qa_data = []

    # 3. 逐批處理
    for batch in tqdm(file_batches, desc="處理檔案批次中"):
        combined_content = ""
        print(f"\n正在處理批次：{', '.join(batch)}")
        
        # 讀取並合併批次中的檔案內容
        for filename in batch:
            filepath = os.path.join(TARGET_DIRECTORY, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    combined_content += f.read() + "\n\n--- (文件分隔線) ---\n\n"
            except Exception as e:
                print(f"警告：讀取檔案 {filename} 失敗，已跳過。錯誤：{e}")

        if not combined_content.strip():
            print("警告：此批次的內容為空，跳過 API 呼叫。")
            continue

        # 4. 呼叫 API 生成問答集
        qa_pairs = generate_qa_for_text(combined_content)
        
        if qa_pairs:
            print(f"成功生成 {len(qa_pairs)} 組問答。")
            all_qa_data.extend(qa_pairs)
        else:
            print(f"處理批次 {batch} 失敗，未生成任何問答。")

    # 5. 將所有結果寫入 JSON 檔案
    if all_qa_data:
        print(f"\n處理完成！總共生成了 {len(all_qa_data)} 組問答。")
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_qa_data, f, ensure_ascii=False, indent=4)
            print(f"結果已成功儲存至 '{os.path.abspath(OUTPUT_FILE)}'。")
        except Exception as e:
            print(f"錯誤：寫入 JSON 檔案失敗。錯誤：{e}")
    else:
        print("\n處理完成，但未生成任何有效的問答資料。")


if __name__ == '__main__':
    main()