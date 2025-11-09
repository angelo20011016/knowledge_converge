# GCP 部署指南：單一虛擬機 + Docker Compose

本文件提供將你的應用程式部署到 GCP Compute Engine 虛擬機的詳細步驟。請按照順序執行，並注意指令是在**本地電腦**執行還是**虛擬機**內執行。

---

## 部署前準備

1.  **GCP 專案與 VM**：
    *   確保你已在 GCP Console 中建立好專案。
    *   確保你已在正確的專案中建立好 VM 執行個體 (例如 `angelo-gcp-vm`，區域 `asia-east1-c`)。

2.  **本地電腦安裝 `gcloud` CLI**：
    *   確保你的 Mac Mini 已安裝並初始化 `gcloud` CLI。
    *   `gcloud init` 已完成，並設定好預設專案、區域和區域。

3.  **專案程式碼**：
    *   確保你的專案程式碼已推送到一個 Git 儲存庫 (例如 GitHub)。
    *   確保你的本地專案根目錄下有 `.env` 檔案。

4.  **`.env` 檔案檢查 (重要！)**：
    *   打開你本地專案根目錄下的 `.env` 檔案。
    *   **`FLASK_SECRET_KEY`**：請務必將 `YOUR_VERY_LONG_RANDOM_SECRET_KEY_HERE` 替換為一個**非常長、隨機且獨一無二的字串**。這對應用程式的安全性至關重要。
    *   確認 `FRONTEND_URL` 和 `GOOGLE_REDIRECT_URI` 都設定為 `https://noledge.happywecan.com`。
    *   確認 `REACT_APP_API_BASE_URL` 也設定為 `https://noledge.happywecan.com`。

---

## 部署步驟

### **第一步：連線到你的 GCP 虛擬機**

在你的**本地 Mac Mini 終端機**中執行：

```bash
gcloud compute ssh angelo-gcp-vm --zone=asia-east1-c
```
*   如果這是第一次連線，`gcloud` 會為你生成 SSH 金鑰。在提示 `Enter passphrase` 時，直接按 Enter 鍵留空即可。

### **第二步：在虛擬機上安裝 Docker 和 Docker Compose**

連線成功後，你將進入 VM 的命令列介面 (`angelo@angelo-gcp-vm:~# GCP 部署指南：單一虛擬機 + Docker Compose

本文件提供將你的應用程式部署到 GCP Compute Engine 虛擬機的詳細步驟。請按照順序執行，並注意指令是在**本地電腦**執行還是**虛擬機**內執行。

---

## 部署前準備

1.  **GCP 專案與 VM**：
    *   確保你已在 GCP Console 中建立好專案。
    *   確保你已在正確的專案中建立好 VM 執行個體 (例如 `angelo-gcp-vm`，區域 `asia-east1-c`)。

2.  **本地電腦安裝 `gcloud` CLI**：
    *   確保你的 Mac Mini 已安裝並初始化 `gcloud` CLI。
    *   `gcloud init` 已完成，並設定好預設專案、區域和區域。

3.  **專案程式碼**：
    *   確保你的專案程式碼已推送到一個 Git 儲存庫 (例如 GitHub)。
    *   確保你的本地專案根目錄下有 `.env` 檔案。

4.  **`.env` 檔案檢查 (重要！)**：
    *   打開你本地專案根目錄下的 `.env` 檔案。
    *   **`FLASK_SECRET_KEY`**：請務必將 `YOUR_VERY_LONG_RANDOM_SECRET_KEY_HERE` 替換為一個**非常長、隨機且獨一無二的字串**。這對應用程式的安全性至關重要。
    *   確認 `FRONTEND_URL` 和 `GOOGLE_REDIRECT_URI` 都設定為 `https://noledge.happywecan.com`。
    *   確認 `REACT_APP_API_BASE_URL` 也設定為 `https://noledge.happywecan.com`。

---

## 部署步驟

### **第一步：連線到你的 GCP 虛擬機**

在你的**本地 Mac Mini 終端機**中執行：

```bash
gcloud compute ssh angelo-gcp-vm --zone=asia-east1-c
```
*   如果這是第一次連線，`gcloud` 會為你生成 SSH 金鑰。在提示 `Enter passphrase` 時，直接按 Enter 鍵留空即可。

)。請在**虛擬機內**執行以下指令：

```bash
# 1. 更新套件列表
sudo apt-get update

# 2. 安裝 Docker 的必要套件
sudo apt-get install ca-certificates curl gnupg -y

# 3. 新增 Docker 的官方 GPG 金鑰 (使用 apt-key add 方式，以解決特殊環境問題)
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 4. 將 Docker 儲存庫新增到 Apt 來源 (注意：這裡強制使用 "jammy" 代號，對應 Ubuntu 22.04 LTS)
echo "deb [arch="$(dpkg --print-architecture)"] https://download.docker.com/linux/ubuntu jammy stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 再次更新套件列表 (包含 Docker 儲存庫)
sudo apt-get update

# 6. 安裝 Docker Engine 和 Docker Compose Plugin
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# 7. 將你的使用者帳戶加入 docker 群組 (這樣就不需要每次都使用 sudo)
sudo usermod -aG docker $USER

# 8. 登出並重新登入 VM，讓群組變更生效
#    請在 VM 終端機輸入 exit 登出，然後重新執行 gcloud compute ssh angelo-gcp-vm --zone=asia-east1-c 連線
```

**重新連線到 VM 後**，你可以執行 `docker run hello-world` 來測試 Docker 是否安裝成功。

### **第三步：複製你的專案儲存庫**

在**虛擬機內**，執行以下指令：

```bash
git clone [你的專案Git網址]
cd knowledge_converge # 進入你的專案目錄
```
*   請將 `[你的專案Git網址]` 替換為你專案的實際 Git 網址。

### **第四步：傳輸 `.env` 檔案和 `data/project.db` (如果需要)**

回到你的**本地 Mac Mini 終端機** (不要在 VM 裡面)，執行以下指令來傳輸檔案：

1.  **傳輸 `.env` 檔案**：
    ```bash
    gcloud compute scp /Users/angelo/Projects/knowledge_converge/.env angelo-gcp-vm:~/knowledge_converge/
    ```

2.  **傳輸 `data/project.db` (如果你想保留舊資料)**：
    *   首先，在**虛擬機內**建立 `data` 目錄：
        ```bash
        mkdir -p ~/knowledge_converge/data
        ```
    *   然後，在**本地 Mac Mini 終端機**執行傳輸指令：
        ```bash
        gcloud compute scp /Users/angelo/Projects/knowledge_converge/data/project.db angelo-gcp-vm:~/knowledge_converge/data/
        ```

### **第五步：啟動應用程式**

回到你的 **虛擬機終端機**，進入專案目錄 (`cd knowledge_converge`)，然後執行以下指令來啟動應用程式：

```bash
docker compose up --build -d
```
*   `--build` 會確保 Docker 重新建立映像檔，包含所有最新的程式碼變更。
*   `-d` 會讓容器在背景運行。

### **第六步：驗證部署**

1.  在 GCP Console 的「VM 執行個體」列表中，找到你的 VM 的「**外部 IP 位址**」。
2.  在你的瀏覽器中，輸入這個外部 IP 位址。
3.  你應該會看到你的前端應用程式。嘗試登入並使用分析功能。

---

## 額外：轉移 Cloudflare Tunnel (如果你使用自訂網域)

如果你想使用自訂網域 (例如 `https://noledge.happywecan.com`)，你需要將你的 Cloudflare Tunnel (`cloudflared`) 服務從你的 Mac Mini 轉移到這台 GCP 虛擬機上。

### **第一步：在 GCP VM 上安裝 `cloudflared`**

請在**虛擬機內**執行以下指令來安裝 `cloudflared`：

```bash
# 1. 下載 Cloudflare GPG 金鑰
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null

# 2. 新增 Cloudflare 儲存庫
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg arch=$(dpkg --print-architecture)] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list >/dev/null

# 3. 更新套件列表
sudo apt-get update

# 4. 安裝 cloudflared
sudo apt-get install cloudflared -y
```

### **第二步：登入 Cloudflare Tunnel**

在**虛擬機內**執行以下指令，並按照提示在瀏覽器中登入你的 Cloudflare 帳號：

```bash
cloudflared tunnel login
```
*   這會下載 `cert.pem` 憑證檔案到 `~/.cloudflared/` 目錄。

### **第三步：傳輸 `config.yml` 和 `credentials-file`**

回到你的**本地 Mac Mini 終端機** (不要在 VM 裡面)，執行以下指令來傳輸檔案：

1.  **傳輸 `config.yml`**：
    ```bash
    gcloud compute scp /Users/angelo/Projects/knowledge_converge/config.yml angelo-gcp-vm:~/knowledge_converge/
    ```

2.  **傳輸 `credentials-file`**：
    *   你的 `credentials-file` 通常位於 `~/.cloudflared/` 目錄下，檔名是你的 Tunnel UUID (例如 `b609df34-a8ce-4333-bf96-d3cb3d6ea2c7.json`)。
    *   請先在 VM 上建立 `~/.cloudflared/` 目錄：
        ```bash
        # 在 VM 內執行
        mkdir -p ~/.cloudflared/
        ```
    *   然後，在**本地 Mac Mini 終端機**執行傳輸指令：
        ```bash
        gcloud compute scp ~/.cloudflared/b609df34-a8ce-4333-bf96-d3cb3d6ea2c7.json angelo-gcp-vm:/home/angelo/.cloudflared/
        ```

### **第四步：設定 `cloudflared` 為系統服務**

我們需要將 `cloudflared` 設定為一個系統服務，這樣它就能在背景持續運行，即使你關閉 SSH 連線，甚至 VM 重啟後，它也會自動啟動。

1.  **停止目前正在運行的 `cloudflared`** (如果有的話，按下 `Ctrl + C`)。

2.  **編輯 VM 上的 `config.yml` 檔案**：
    *   在 VM 終端機中，執行以下指令來編輯 `config.yml`：
        ```bash
        nano ~/knowledge_converge/config.yml
        ```
    *   找到 `credentials-file` 那一行，將其修改為：
        ```yaml
        credentials-file: /home/angelo/.cloudflared/b609df34-a8ce-4333-bf96-d3cb3d6ea2c7.json
        ```
        *   請將 `b609df34-a8ce-4333-bf96-d3cb3d6ea2c7.json` 替換為你實際的憑證檔名。
    *   儲存並退出 `nano` (按下 `Ctrl + O`，Enter，然後 `Ctrl + X`)。

3.  **建立 `cloudflared` 服務檔案**：
    *   使用 `nano` 編輯器建立一個新的服務檔案：
        ```bash
        sudo nano /etc/systemd/system/cloudflared.service
        ```

4.  **貼上以下內容到 `cloudflared.service` 檔案中**：
    *   請將 `[你的Tunnel名稱]` 替換為你實際的 Tunnel 名稱 (例如 `vkc-tunnel`)。
    *   請將 `b609df34-a8ce-4333-bf96-d3cb3d6ea2c7.json` 替換為你實際的憑證檔名。
    ```ini
    [Unit]
    Description=Cloudflare Tunnel
    After=network.target

    [Service]
    TimeoutStartSec=0
    Type=simple
    User=angelo
    ExecStart=/usr/local/bin/cloudflared tunnel --config /home/angelo/knowledge_converge/config.yml run vkc-tunnel
    Restart=on-failure
    RestartSec=5s

    [Install]
    WantedBy=multi-user.target
    ```
    *   儲存並退出 `nano`。

5.  **重新載入 systemd 配置**：
    ```bash
    sudo systemctl daemon-reload
    ```

6.  **啟用並啟動 `cloudflared` 服務**：
    ```bash
    sudo systemctl enable cloudflared
    sudo systemctl start cloudflared
    ```

7.  **檢查服務狀態**：
    ```bash
    sudo systemctl status cloudflared
    ```
    *   你應該會看到 `Active: active (running)` 的字樣。

### **第五步：驗證**

*   在你的瀏覽器中，訪問你的自訂網域 `https://noledge.happywecan.com`。
*   你應該會看到你的應用程式，並且登入功能也能正常使用了。



  關閉 VM 的指令：

  在你的本地 Mac Mini 終端機中執行：

   1 gcloud compute instances stop vkc-vm --zone=asia-east1-c
   * 當你需要再次啟動 VM 時，執行：
   1     gcloud compute instances start vkc-vm --zone=asia-east1-c


   #docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
