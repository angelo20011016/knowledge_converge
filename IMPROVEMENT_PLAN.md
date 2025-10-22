# 專案 "knowledge_converge" 穩定性與健壯性改善計畫

這份文件旨在全面分析 `knowledge_converge` 專案當前遇到的問題，並提供一個一次性的、完整的修復方案與執行清單。

## 第一部分：問題根源總結

經過之前的多次測試與日誌分析，我們共同定位到了導致應用不穩定、浪費 API 費用及前端無回應的五個核心問題：

1.  **【最關鍵】服務意外重啟**: 後端服務以除錯模式 (`debug=True`) 運行，此模式下的「自動重載」功能會在背景任務寫入分析檔案時，誤判為程式碼變更而重啟服務，從而**強行終止正在運行的分析執行緒**。這是導致 API 費用被浪費但結果卻丟失的直接原因。

2.  **並發請求衝突**: 整個應用程式使用全域變數（`current_status`, `analysis_context`）來追蹤單一任務的狀態。這在多使用者或多分頁同時請求時，會導致狀態互相覆蓋，造成進度與結果的錯亂。

3.  **靜默失敗與錯誤鏈中斷**: 專案的許多核心功能模組（如音訊下載、語音轉錄、總結分析）在內部發生錯誤時，僅僅印出一條日誌就返回 `None` 或直接忽略 (`pass`)，而不是將「錯誤」這個信號傳遞給上層呼叫者。這導致主流程無法感知到失敗，表現為「卡住」或「沒有任何反應」。

4.  **過時的 API 使用方式**: `transcribe_wav.py` 中使用了 `genai.upload_file()`，這在您目前安裝的 Google 函式庫版本中是不正確的用法，它現在專用於 RAG 功能，因此導致了 `ragStoreName` 參數缺失的錯誤。

5.  **資源洩漏**: 處理流程中從 YouTube 下載的 `.wav` 音訊檔在處理完畢後沒有被刪除，會永久佔用伺服器儲存空間。

---

## 第二部分：完整修復方案與執行清單

以下是針對上述所有問題的、一次性的完整修復清單。

### A. 核心架構修正 (`app.py`)

- [ ] **禁用自動重載 (最高優先級)**
    - **目標**: 防止服務意外重啟，解決 API 浪費問題。
    - **操作**: 修改 `app.py` 的最後一行，在 `app.run()` 中加入 `use_reloader=False`。
    - **修改前**: `app.run(debug=True, port=5000)`
    - **修改後**: `app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)`

- [ ] **實作 Job ID 隔離系統**
    - **目標**: 解決並發請求衝突問題。
    - **操作**:
        1.  移除全域變數 `current_status` 和 `analysis_context`。
        2.  在 `app.py` 頂層建立一個全域的 `JOBS = {}` 字典。
        3.  修改 API 路由（例如 `/api/summarize-url`），使其在收到請求時：
            - 用 `uuid` 函式庫生成一個唯一的 `job_id`。
            - 在 `JOBS` 字典中初始化一個位置：`JOBS[job_id] = {"status": ..., "result": None}`。
            - 將 `job_id` 傳遞給背景執行緒。
            - 立即將 `job_id` 回傳給前端。
        4.  建立一個新的 API 路由 `/api/get-job-result/<job_id>`，供前端根據 `job_id` 安全地查詢特定任務的狀態和結果。
        5.  在背景執行緒的最後，加入邏輯，將 `main.py` 回傳的檔案**路徑**讀取為檔案**內容**，轉換為前端需要的 `final_content` 格式後再存入 `JOBS` 字典。

### B. 子模組修正 (`modules/`)

- [ ] **修正錯誤處理方式**
    - **目標**: 打通錯誤傳遞鏈，拒絕靜默失敗。
    - **操作**:
        1.  在 `transcribe_wav.py` 的 `except` 區塊中，將 `return None` 改為 `raise e`。
        2.  在 `download_YTvideo2wav.py` 的 `except` 區塊中，將 `return None` 改為 `raise e`。
        3.  在 `analyze_transcript_with_gemini.py` 的 `except` 區塊中，將 `pass` 改為 `raise e`。

- [ ] **修正 `transcribe_wav.py` 中的 API 用法**
    - **目標**: 解決 `ragStoreName` 錯誤。
    - **操作**: 移除 `genai.upload_file()` 的呼叫，改為先讀取檔案的二進位內容，然後將 `{'mime_type': 'audio/wav', 'data': ...}` 這樣的字典直接傳遞給 `model.generate_content_async()`。

### C. 主流程修正 (`main.py`)

- [ ] **適應 Job ID 系統**
    - **目標**: 讓主流程能在隔離的環境中運作。
    - **操作**: 修改 `run_analysis_for_url` 等函式的定義，讓它可以接收 `job_id`，並使用此 ID 來建立唯一的輸出資料夾路徑（例如 `output/jobs/<job_id>/`）。

- [ ] **加入資源清理**
    - **目標**: 解決資源洩漏問題。
    - **操作**: 在 `run_analysis_for_url` 中使用 `try...finally` 結構，確保在 `finally` 區塊中執行 `os.remove(audio_path)`，刪除已處理完的 `.wav` 檔案。

- [ ] **捕捉與回傳錯誤**
    - **目標**: 讓主流程能應對底層的失敗。
    - **操作**: 在 `run_analysis_for_url` 的主 `try` 區塊中，加入 `except Exception as e:`。當捕捉到底層模組拋出的異常時，不再讓程式崩潰，而是回傳一個結構化的錯誤字典，例如 `return {"status": "error", "message": str(e)}`。

### D. 前端修正 (`frontend/src/pages/`)

- [ ] **更新 API 呼叫邏輯**
    - **目標**: 對接新的 Job ID 工作流程。
    - **操作**:
        1.  修改 `handleSubmit` 函式，將 `fetch` 請求指向新的「啟動任務」API 位址 (例如 `/api/start-url-summary`)。
        2.  在收到回應後，從 JSON 中儲存回傳的 `job_id`。
        3.  啟動一個輪詢函式 (`setInterval`)，該函式會定期使用 `job_id` 去請求新的「查詢結果」API 位址 (`/api/get-job-result/<job_id>`)。
        4.  根據查詢回傳的 `status` 欄位（`running`, `success`, `error`）來更新載入動畫、結果或錯誤訊息。

---

## 第三部分：結論與後續步驟

這份文件詳細列出了所有需要執行的修改，構成了一個完整、系統性的解決方案。

建議的執行順序為：**B. 子模組 -> C. 主流程 -> A. 核心架構 -> D. 前端**。

請您審閱此計畫。在您完全理解並同意後，我們可以再決定下一步是由我來執行這些修改，還是您希望根據這份文件自行操作。
