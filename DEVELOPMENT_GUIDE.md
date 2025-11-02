# 更新後的開發與部署指南

為了確保專案在不同機器間部署時資料的持久性，我們已經將資料庫從 Docker 具名磁碟區 (named volume) 改為**主機路徑掛載 (host-bind mount)**。這表示 `project.db` 檔案現在會直接儲存在你專案根目錄下的 `data/` 資料夾中。

## 在新機器上設定專案的步驟

1.  **複製專案程式碼：**
    ```bash
    git clone <你的專案Git網址>
    cd Video_Knowledge_Convergence
    ```

2.  **安裝 Docker 和 Docker Compose：**
    確保你的新機器上已經安裝了 Docker 和 Docker Compose。

3.  **建立 `.env` 檔案：**
    在專案的根目錄中建立一個 `.env` 檔案。這個檔案用於儲存環境變數，**絕不能提交到 Git**。

4.  **配置 `.env` 檔案：**
    將以下內容新增到 `.env` 檔案中。請根據你的環境（本地開發或生產部署）填寫正確的 URL 和 Google OAuth 憑證。

    ```
    # --- Google OAuth 憑證 ---
    GOOGLE_CLIENT_ID=<你的Google Client ID>
    GOOGLE_CLIENT_SECRET=<你的Google Client Secret>

    # --- 管理員設定 ---
    # 你的 Google 帳號 ID，用於登入管理後台。
    ADMIN_GOOGLE_ID=<你的管理員Google ID>
    
    # --- Flask Secret Key ---
    FLASK_SECRET_KEY=<請填入一個隨機的長字串>

    # --- 本地開發 ---
    FRONTEND_URL=http://localhost:3000
    REACT_APP_API_BASE_URL=http://localhost:5001
    GOOGLE_REDIRECT_URI=http://localhost:5001/api/auth

    # --- 生產部署 (範例，請替換為你的實際網域) ---
    # FRONTEND_URL=https://noledge.happywecan.com
    # REACT_APP_API_BASE_URL=https://noledge.happywecan.com
    # GOOGLE_REDIRECT_URI=https://noledge.happywecan.com/api/auth
    ```

5.  **配置 Google Cloud Console：**
    前往你的 Google Cloud Console -> API與服務 -> 憑證。
    *   找到你的 OAuth 2.0 Client ID。
    *   將 `http://localhost:5001/api/auth` (本地開發) 和/或 `https://你的網域/api/auth` (生產部署) 新增到**授權重定向 URI** 列表中。

6.  **複製資料庫檔案 (如果需要保留舊資料)：**
    如果你想在新機器上繼續使用舊的資料（例如，現有的使用者和他們的用量限制），你需要將舊機器上專案根目錄下的 `data/` 資料夾完整複製到新機器的專案根目錄下。如果不需要保留舊資料，則可以跳過此步驟，Docker 會自動建立一個新的空資料庫。

7.  **啟動應用程式：**
    在專案根目錄下執行以下命令。`--build` 參數會確保 Docker 重新建立映像，包含所有最新的程式碼變更。
    ```bash
    docker-compose up -d --build
    ```

8.  **執行資料庫遷移 (僅在新資料庫或有模型變更時需要)：**
    如果這是第一次啟動，或者你對 `models.py` 進行了修改，你需要執行資料庫遷移來更新資料庫結構。
    ```bash
    docker-compose exec backend flask db upgrade
    ```
    **注意：** 如果你從舊機器複製了 `data/project.db` 過來，並且舊資料庫的結構與當前程式碼的 `models.py` 不符，`flask db upgrade` 會嘗試將其升級到最新版本。
