# 知識匯聚專案

## 專案概述
本專案旨在根據使用者提供的主題，自動化從 YouTube 影片中收集資訊的過程。它涉及搜尋相關影片、提取或轉錄其內容，然後利用 Google 的 Gemini AI 模型進行深入分析、摘要和關鍵資訊提取。最終目標是從多個影片來源為給定主題提供一個整合且有用的摘要。

## 工作流程（目前狀態）

`main.py` 腳本協調以下步驟：

### 步驟 1：URL 檢索 (`step1_get_urls`)
-   使用者提供一個中文主題查詢。
-   系統在必要時將查詢翻譯成英文以擴大搜尋範圍。
-   它會搜尋 YouTube 上與中文和英文查詢相關的影片。
-   影片 URL 和元資料會儲存到 `Question/<query_folder_name>/urls.json`。
-   在 `Question/<query_folder_name>/` 中建立必要的目錄 (`subs/`、`audio_files/`、`transcripts/`) 以儲存中間輸出。

### 步驟 2：轉錄稿生成（官方 CC 與音訊 STT）
對於步驟 1 中識別的每個影片，系統會嘗試生成轉錄稿：

#### 2.1 嘗試官方字幕 (CC)
-   系統首先嘗試使用 `yt_get_cc.get_subtitle` 下載官方字幕。
-   如果成功，VTT 檔案會使用 `yt_transcription_re.clean_vtt_file` 進行清理和處理。
-   清理後的轉錄稿路徑會儲存在 `video['transcript_path']` 中。

#### 2.2 如果官方字幕失敗或未找到
-   影片會被添加到音訊下載佇列中。
-   使用 `download_YTvideo2wav.download_audio` 下載這些影片的音訊。
-   然後使用 `transcribe_wav.transcribe_audio_single`（語音轉文字）轉錄下載的音訊。
-   轉錄後的路徑會儲存在 `video['transcript_path']` 中。

### 步驟 3：單個轉錄稿 AI 分析（模組 1：`analyze_transcript_with_gemini`）
-   **觸發：** 在成功獲取單個影片的 `video['transcript_path']` 後（無論是來自官方 CC 還是音訊 STT），此模組會立即被呼叫。
-   **動作：** 單個轉錄稿的內容會發送給 `gemini-2.5-flash-lite` 模型。AI 會對該單個轉錄稿執行詳細的內容分析、組織，並提取有用的資訊。
-   **輸出：** 會建立一個新的子資料夾 `Question/<query_folder_name>/summary/<video_id>/`。AI 的詳細分析會儲存在此子資料夾中的 `analysis.txt`。

### 步驟 4：合併 AI 分析（模組 2：`combine_and_extract_final_info`）
-   **觸發：** 在 `videos_to_process` 列表中的所有影片都完成了轉錄稿生成和單個 AI 分析（步驟 3）後，此模組會被呼叫。
-   **動作：** 它會讀取 `Question/<query_folder_name>/summary/*/` 子資料夾中的所有 `analysis.txt` 檔案，合併它們的內容，並將此合併後的文本發送給 `gemini-2.5-flash-lite` 模型。AI 的任務是從聚合內容中提取重要資訊和節錄。
-   **輸出：** 最終提取的資訊會儲存到 `Question/<query_folder_name>/final_extracted_info.txt`。

## AI 交接

### 目前狀態
-   影片處理的核心工作流程（URL 檢索、透過 CC 或 STT 生成轉錄稿）已建立。
-   兩個新的 AI 模組（`analyze_transcript_with_gemini.py` 和 `combine_and_extract_final_info.py`）已開發完成，並準備好整合到 `main.py` 中。
-   `main.py` 已準備好一個 `SIMULATE_AI_PROCESSING` 標誌，允許在不進行實際 API 呼叫的情況下進行模擬運行，便於測試和驗證整合點和檔案路徑。

### 下一個 AI 的後續步驟
1.  **將 AI 模組整合到 `main.py` 中：**
    *   **`analyze_transcript_with_gemini`：** 在 `main.py` 中，在官方 CC 處理區塊和音訊 STT 處理區塊中，在成功確定 `video['transcript_path']` 後，立即插入對此函數的呼叫。確保遵守 `SIMULATE_AI_PROCESSING` 標誌。
    *   **`combine_and_extract_final_info`：** 在 `main.py` 的 `main` 函數的末尾，在所有單個影片處理循環完成後，插入對此函數的呼叫。確保遵守 `SIMULATE_AI_PROCESSING` 標誌。
2.  **測試與驗證：**
    *   運行 `main.py` 並將 `SIMULATE_AI_PROCESSING = True`，以驗證是否觸發了正確的列印語句，以及模擬輸出檔案（`analysis.txt` 和 `final_extracted_info.txt`）是否在預期的目錄結構中建立。
    *   一旦模擬運行得到確認，使用者可以將 `SIMULATE_AI_PROCESSING = False` 並在 `.env` 檔案中提供 `GEMINI_API_KEY` 以執行實際的 AI 處理。
3.  **優化 AI 提示詞（如有必要）：** `analyze_transcript_with_gemini.py` 和 `combine_and_extract_final_info.py` 中的當前提示詞是初始版本。可能需要根據 AI 輸出的品質進行進一步優化。
4.  **錯誤處理和邊緣情況：** 審查並增強錯誤處理，特別是關於 API 呼叫和檔案操作，以使工作流程更健壯。
5.  **性能優化：** 探索性能改進的機會，特別是在 AI 處理步驟中。
