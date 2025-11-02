# Video Knowledge Convergence Project

## Project Overview

The "Video Knowledge Convergence" project is an intelligent system designed to extract and synthesize knowledge from YouTube videos based on user-defined queries. It automates the entire pipeline from video discovery to AI-powered content analysis and summarization, providing users with refined, actionable information.

## Features

*   **Intelligent Video Search:** Finds relevant YouTube videos based on a user query, filtering by criteria like video length and sorting by view count.
*   **Multi-source Transcription:** Prioritizes downloading official subtitles (Closed Captions) for accuracy. If not available, it downloads video audio and performs Speech-to-Text (STT) transcription.
*   **AI-Powered Content Analysis:** Utilizes the Google Gemini AI model to analyze individual video transcripts, extracting useful information.
*   **Knowledge Synthesis:** Combines analyses from multiple videos and performs a final AI-driven extraction to synthesize key insights.
*   **Real-time Status Tracking:** Provides live updates on the analysis progress directly within the frontend user interface.
*   **User-Friendly Interface:** A React-based frontend with a clean, elegant design (inspired by "notebook lm") for easy interaction.

## Project Structure

```
.
├───.gitignore
├───app.py                  # Flask backend application, handles API requests and serves status.
├───main.py                 # Core orchestration logic (run_analysis function).
├───README.md               # This file.
├───status.py               # Global status variable for inter-module communication.
├───audio_multi_process/    # Modules for audio processing.
│   ├───audio_spliter.py    # (Currently not used in main.py) Splits audio files.
│   └───parallel_transcriber.py # (Currently not used in main.py) Parallel transcription.
├───frontend/               # React frontend application.
│   ├───public/             # Static assets.
│   └───src/                # React components (App.js is main).
├───modules/                # Core Python utility modules.
│   ├───cleantranscription.py # Cleans raw transcript text.
│   ├───download_YTvideo2wav.py # Downloads YouTube video audio to WAV.
│   ├───transcribe_wav.py   # Single-threaded audio transcription (faster-whisper).
│   ├───yt_get_cc.py        # Downloads YouTube official subtitles.
│   └───yt_transcription_re.py # Cleans VTT subtitle files.
├───Question/               # Output directory for query-specific results.
├───step1_get_10url/        # Modules for video URL acquisition.
│   └───get_top_10_watched.py # Uses YouTube API to get top videos.
└───step3_AI_summary/       # Modules for AI analysis and summarization.
    ├───analyze_transcript_with_gemini.py # Analyzes single transcripts with Gemini.
    ├───combine_and_extract_final_info.py # Combines analyses and extracts final info.
    └───combine_transcripts.py # (Currently not used in main.py) Combines multiple transcripts.
```

## Project Flow Diagram

詳細的專案流程圖請參考 [docs/flowchart.md](docs/flowchart.md)。

## Setup and Running

### Prerequisites

*   Python 3.9+
*   Node.js & npm
*   FFmpeg (for audio conversion, ensure it's in your system PATH)
*   Google YouTube Data API Key (set as `YOUTUBE_API_KEY` environment variable)
*   Google Gemini API Key (set as `GEMINI_API_KEY` environment variable)

### Backend Setup

1.  **Install Python dependencies:**
    ```bash
    # 影片知識匯聚專案

## 專案概述

「影片知識匯聚」專案是一個智慧系統，旨在根據使用者定義的查詢，從 YouTube 影片中提取和整合知識。它自動化了從影片發現到 AI 驅動的內容分析和摘要的整個流程，為使用者提供精煉、可操作的資訊。

## 功能特色

*   **智慧影片搜尋：** 根據使用者查詢尋找相關的 YouTube 影片，並根據影片長度等標準進行篩選，按觀看次數排序。
*   **多來源轉錄：** 優先下載官方字幕（Closed Captions）以確保準確性。如果不可用，則下載影片音訊並執行語音轉文字（STT）轉錄。
*   **AI 驅動的內容分析：** 利用 Google Gemini AI 模型分析單個影片轉錄稿，提取有用資訊。
*   **知識整合：** 合併來自多個影片的分析結果，並執行最終的 AI 驅動提取，以整合關鍵見解。
*   **即時狀態追蹤：** 在前端使用者介面中直接提供分析進度的即時更新。
*   **使用者友善介面：** 基於 React 的前端，設計簡潔優雅（靈感來自「notebook lm」），便於互動。

## 專案結構

```
.
├───.gitignore
├───app.py                  # Flask 後端應用程式，處理 API 請求並提供狀態。
├───main.py                 # 核心協調邏輯 (run_analysis 函數)。
├───README.md               # 本檔案。
├───status.py               # 用於模組間通訊的全域狀態變數。
├───audio_multi_process/    # 音訊處理模組。
│   ├───audio_spliter.py    # (目前未在 main.py 中使用) 分割音訊檔案。
│   └───parallel_transcriber.py # (目前未在 main.py 中使用) 平行轉錄。
├───frontend/               # React 前端應用程式。
│   ├───public/             # 靜態資源。
│   └───src/                # React 組件 (App.js 為主要)。
├───modules/                # 核心 Python 工具模組。
│   ├───cleantranscription.py # 清理原始轉錄文字。
│   ├───download_YTvideo2wav.py # 下載 YouTube 影片音訊為 WAV。
│   ├───transcribe_wav.py   # 單執行緒音訊轉錄 (faster-whisper)。
│   ├───yt_get_cc.py        # 下載 YouTube 官方字幕。
│   └───yt_transcription_re.py # 清理 VTT 字幕檔案。
├───Question/               # 查詢特定結果的輸出目錄。
├───step1_get_10url/        # 影片網址獲取模組。
│   └───get_top_10_watched.py # 使用 YouTube API 獲取熱門影片。
└───step3_AI_summary/       # AI 分析和摘要模組。
    ├───analyze_transcript_with_gemini.py # 使用 Gemini 分析單個轉錄稿。
    ├───combine_and_extract_final_info.py # 合併分析結果並提取最終資訊。
    └───combine_transcripts.py # (目前未在 main.py 中使用) 合併多個轉錄稿。
```

## 專案流程圖

詳細的專案流程圖請參考 [docs/flowchart.md](docs/flowchart.md)。

## 設定與運行

### 前置條件

*   Python 3.9+
*   Node.js & npm
*   FFmpeg (用於音訊轉換，請確保其在您的系統 PATH 中)
*   Google YouTube Data API Key (設定為環境變數 `YOUTUBE_API_KEY`)
*   Google Gemini API Key (設定為環境變數 `GEMINI_API_KEY`)

### 後端設定

1.  **安裝 Python 依賴：**
    ```bash
    pip install -r requirements.txt # (假設 requirements.txt 存在或自行創建)
    # 如果沒有 requirements.txt，請手動安裝：
    # pip install Flask Flask-Cors yt-dlp google-api-python-client isodate python-dotenv google-generativeai faster-whisper librosa soundfile
    ```
2.  **設定環境變數：** 在專案根目錄創建一個 `.env` 檔案，包含您的 API 金鑰：
    ```
    YOUTUBE_API_KEY="您的_YOUTUBE_API_KEY"
    GEMINI_API_KEY="您的_GEMINI_API_KEY"
    ```
3.  **運行後端：**
    ```bash
    python app.py
    ```

### 前端設定

1.  **進入前端目錄：**
    ```bash
    cd frontend
    ```
2.  **安裝 Node.js 依賴：**
    ```bash
    npm install
    ```
3.  **運行前端：**
    ```bash
    npm start
    ```

### 使用方法

1.  確保後端和前端伺服器都在運行。
2.  在瀏覽器中打開 `http://localhost:3000`。
3.  在輸入框中輸入您感興趣的主題，然後點擊「Analyze」。
4.  觀察即時狀態更新和最終提取的知識。

## 目前已知問題 / 未來改進

*   **大型音訊檔案處理：** 目前的 `transcribe_wav.py` 會將整個音訊檔案載入到記憶體中，這可能導致高磁碟 I/O 並使非常長的影片崩潰。需要一個更穩健的解決方案，涉及音訊分割和基於塊的轉錄（類似於 `parallel_transcriber.py` 但不一次性載入整個音訊）。
*   **錯誤處理：** 增強錯誤處理和報告，以實現更優雅的故障。
*   **臨時檔案清理：** 實施一種機制，在成功處理後清理臨時音訊和轉錄檔案。
*   **可擴展性：** 考慮使用非同步處理或訊息佇列來處理長時間運行的任務。
*   **UI/UX 優化：** 進一步優化前端設計和使用者體驗。

    ```
2.  **Set Environment Variables:** Create a `.env` file in the project root with your API keys:
    ```
    YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
3.  **Run the Backend:**
    ```bash
    python app.py
    ```

### Frontend Setup

1.  **Navigate to frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```
3.  **Run the Frontend:**
    ```bash
    npm start
    ```

### Usage

1.  Ensure both backend and frontend servers are running.
2.  Open your browser to `http://localhost:3000`.
3.  Enter a topic of interest in the input field and click "Analyze".
4.  Observe the real-time status updates and the final extracted knowledge.

## Current Known Issues / Future Improvements

*   **Large Audio File Processing:** The current `transcribe_wav.py` loads entire audio files into memory, which can lead to high disk I/O and crashes for very long videos. A more robust solution involving audio splitting and chunk-based transcription (similar to `parallel_transcriber.py` but without loading the whole audio at once) is needed.
*   **Error Handling:** Enhance error handling and reporting for more graceful failures.
*   **Temporary File Cleanup:** Implement a mechanism to clean up temporary audio and transcript files after successful processing.
*   **Scalability:** Consider using asynchronous processing or message queues for long-running tasks.
*   **UI/UX Refinements:** Further refine the frontend design and user experience.

### Accessing the Admin Panel

The admin panel is protected and accessible only to the designated administrator via Google SSO.

1.  **Set Admin Password:**
    *   In your `.env` file, add the following line and replace the example ID with your own Google Account ID:
        ```
        ADMIN_GOOGLE_ID="107490620158118092089"
        ```
    *   You can find your Google ID by logging into a Google service and visiting a site like `https://developers.google.com/people/api/rest/v1/people/get` (click "Execute" for `people/me`). Your ID is the 21-digit number in the `resourceName` field (`people/YOUR_ID`).

2.  **Access the Interface:**
    *   Open your web browser and navigate to `http://localhost:5001/admin`.
    *   If you are not logged in, you will be automatically redirected to the Google login page.
    *   Log in with the Google account whose ID matches the `ADMIN_GOOGLE_ID`.
    *   After successful login, you will be granted access to the admin panel.
