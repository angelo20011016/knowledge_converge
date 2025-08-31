# 知識匯聚專案

## 專案概述
本專案旨在根據使用者提供的主題，自動化從 YouTube 影片中收集資訊的過程。它涉及搜尋相關影片、提取或轉錄其內容，然後利用 Google 的 Gemini AI 模型進行深入分析、摘要和關鍵資訊提取。最終目標是從多個影片來源為給定主題提供一個整合且有用的摘要。

## 工作流程詳解

`main.py` 腳本協調以下主要步驟：

### 步驟 1：URL 檢索 (`step1_get_10url/get_top_10_watched.py`)
-   **功能：** 根據使用者輸入的中文主題查詢，搜尋 YouTube 上的相關影片。如果需要，查詢會被翻譯成英文以擴大搜尋範圍。
-   **輸入：** 使用者提供的中文主題。
-   **輸出：** 影片 URL 和元資料會儲存到 `Question/<query_folder_name>/urls.json`。同時，會在 `Question/<query_folder_name>/` 下建立 `subs/`、`audio_files/`、`transcripts/` 和 `summary/` 等必要目錄。

### 步驟 2：轉錄稿生成（官方 CC 與音訊 STT）
對於步驟 1 中識別的每個影片，系統會嘗試生成轉錄稿。

#### 2.1 嘗試官方字幕 (`modules/yt_get_cc.py` & `modules/yt_transcription_re.py`)
-   **功能：** 系統首先嘗試使用 `yt_get_cc.get_subtitle` 下載影片的官方字幕。如果成功，VTT 檔案會使用 `yt_transcription_re.clean_vtt_file` 進行清理和處理。
-   **觸發：** 在 `main.py` 中，針對每個影片。
-   **輸出：** 清理後的轉錄稿路徑會儲存在 `video['transcript_path']` 中。成功獲取官方字幕後，會立即觸發單個轉錄稿的 AI 分析（步驟 3）。

#### 2.2 如果官方字幕失敗或未找到 (`modules/download_YTvideo2wav.py` & `modules/transcribe_wav.py`)
-   **功能：** 如果沒有找到官方字幕或下載失敗，影片會被添加到音訊下載佇列中。然後使用 `download_YTvideo2wav.download_audio` 下載這些影片的音訊，並使用 `transcribe_wav.transcribe_audio_single` 進行語音轉文字 (STT) 轉錄。
-   **觸發：** 在 `main.py` 中，當官方字幕獲取失敗時。
-   **輸出：** 轉錄後的路徑會儲存在 `video['transcript_path']` 中。成功音訊轉錄後，會立即觸發單個轉錄稿的 AI 分析（步驟 3）。

### 步驟 3：單個轉錄稿 AI 分析 (`step3_AI_summary/analyze_transcript_with_gemini.py`)
-   **功能：** 將單個影片的轉錄稿內容發送給 `gemini-2.5-flash-lite` 模型，進行詳細的內容分析、組織和有用資訊提取。
-   **觸發：** 在 `main.py` 中，成功獲取單個影片的 `video['transcript_path']` 後（無論是來自官方 CC 還是音訊 STT），此模組會立即被呼叫。
-   **輸出：** AI 的詳細分析會儲存為 `<video_id>.txt` 檔案，直接位於 `Question/<query_folder_name>/summary/` 目錄下。

### 步驟 4：合併 AI 分析 (`step3_AI_summary/combine_and_extract_final_info.py`)
-   **功能：** 讀取 `Question/<query_folder_name>/summary/` 目錄中的所有單個分析檔案（`<video_id>.txt`），合併它們的內容，並將此聚合文本發送給 `gemini-2.5-flash-lite` 模型。AI 的任務是從聚合內容中提取重要的資訊和節錄。
-   **觸發：** 在 `main.py` 中，當 `videos_to_process` 列表中的所有影片都完成了轉錄稿生成和單個 AI 分析（步驟 3）後，此模組會被呼叫。
-   **輸出：** 最終提取的資訊會儲存到 `Question/<query_folder_name>/final_extracted_info.txt`。

## 支援模組
-   `modules/cleantranscription.py`: 提供清理原始轉錄文本（例如，移除時間戳）的功能。
-   `modules/summarize_transcripts.py`: (目前在 `main.py` 的主要流程中未使用，但提供分析轉錄字數的功能)。
-   `audio_multi_process/audio_spliter.py`: 提供將音訊檔案分割成塊的功能。(目前在 `main.py` 的主要流程中未使用)。
-   `audio_multi_process/parallel_transcriber.py`: 提供並行音訊轉錄的功能。(目前在 `main.py` 的主要流程中未使用，`transcribe_wav.py` 用於單執行緒轉錄)。

## 配置
-   `SIMULATE_AI_PROCESSING` 標誌 (`main.py`): 控制是否進行實際 AI API 呼叫 (`False`) 或模擬處理 (`True`)。
-   `GEMINI_API_KEY` (`.env` 檔案): 進行實際 AI 處理所需。
-   `YOUTUBE_API_KEY` (`.env` 檔案): 進行 YouTube API 搜尋所需。

## 如何運行
1.  確保您已安裝所有必要的 Python 套件 (參考 `requirements.txt` 或專案依賴)。
2.  在專案根目錄下建立 `.env` 檔案，並設定 `GEMINI_API_KEY` 和 `YOUTUBE_API_KEY`。
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY"
    ```
3.  運行 `main.py` 腳本：
    ```bash
    python main.py
    ```
4.  按照提示輸入您想搜尋的中文主題。

## 注意事項
-   `SIMULATE_AI_PROCESSING` 預設為 `False`，表示會進行實際的 AI 呼叫。如果您想在不消耗 API 配額的情況下測試流程，請將其設定為 `True`。
-   音訊轉錄 (STT) 可能需要較長時間，具體取決於音訊長度和模型大小。
-   請確保您的環境已正確配置 `ffmpeg`，以便 `yt-dlp` 能夠正確處理音訊轉換。