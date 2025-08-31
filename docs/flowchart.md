```mermaid
graph TD
    A[使用者輸入查詢] --> B{後端: app.py /analyze};
    B --> C[main.py: run_analysis(查詢)];

    C --> C1[初始化狀態與環境];
    C1 --> C2[步驟 1: 獲取影片網址 (get_top_10_watched.py)];
    C2 --> C3{迴圈: 處理每個影片};

    C3 --> D1{有官方字幕嗎?};
    D1 -- 是 --> E1[下載字幕 (yt_get_cc.py)];
    E1 --> F1[清理 VTT (yt_transcription_re.py)];
    F1 --> G1[AI 分析轉錄稿 (analyze_transcript_with_gemini.py)];
    G1 --> H1[儲存單獨分析結果];

    D1 -- 否 --> D2[下載音訊 (download_YTvideo2wav.py)];
    D2 --> E2[轉錄音訊 (transcribe_wav.py)];
    E2 --> G1; % 重複使用 AI 分析步驟

    C3 --> I[結束迴圈];
    I --> J[步驟 2: 合併並提取最終資訊 (combine_and_extract_final_info.py)];
    J --> K[儲存最終提取資訊];
    K --> L{後端: app.py /analyze};
    L --> M[返回最終內容至前端];

    subgraph 狀態更新
        N[main.py 更新 current_status] --> O[app.py /status 端點];
        O --> P[前端輪詢 /status];
        P --> Q[在 UI 上顯示狀態];
    end
```