開發與部署指南
這個專案使用環境變數來管理本地開發和生產部署的不同配置。這使得相同的程式碼庫可以在不同的環境中運行，而無需修改程式碼。

這個系統的核心是.env檔案，它儲存了這些環境特定的變數。

重要提示： .env檔案絕不應該提交到Git。它已經列在.gitignore檔案中，以防止意外提交。

本地開發
適用於在您的本地機器（Windows、macOS 或 Linux）上進行開發。

在專案的根目錄中建立一個.env檔案。
將以下內容新增到.env檔案中。這將配置應用程式在您的本地機器上運行：
code
Bash
# --- 本地開發 ---

# 您的前端應用程式的公共URL
FRONTEND_URL=http://localhost:3000

# 前端向後端發出API呼叫的基礎URL
# 這應該與docker-compose.yml中的端口映射相符（例如："5001:5000"）
REACT_APP_API_BASE_URL=http://localhost:5001

# 後端的Google OAuth重定向URI
GOOGLE_REDIRECT_URI=http://localhost:5001/api/auth
配置Google Cloud Console：
前往您的Google Cloud Console -> API與服務 -> 憑證。
找到您的OAuth 2.0 Client ID。
將http://localhost:5001/api/auth新增到授權重定向URI列表中。這是Google登入在本地運作所必需的。
運行應用程式：
code
Bash
docker-compose up -d --build
生產部署
用於將應用程式部署到公共伺服器，例如noledge.happywecan.com。

在您的生產伺服器上，在專案的根目錄中建立一個.env檔案。
將以下內容新增到檔案中，將https://noledge.happywecan.com替換為您實際的公共網域：
code
Bash
# --- 生產部署 ---

# 您的前端應用程式的公共URL
FRONTEND_URL=https://noledge.happywecan.com

# 前端向後端發出API呼叫的基礎URL
REACT_APP_API_BASE_URL=https://noledge.happywecan.com

# 後端的Google OAuth重定向URI
GOOGLE_REDIRECT_URI=https://noledge.happywecan.com/api/auth
配置Google Cloud Console：
確保https://noledge.happywecan.com/api/auth在您的Google Cloud Console的授權重定向URI列表中。
運行應用程式：
code
Bash
docker-compose up -d --build
跨作業系統相容性
由於此專案使用Docker和.env檔案進行配置，因此開發和部署過程在不同作業系統（Windows、macOS、Linux）之間是相同的。您無需更改任何命令或程式碼即可在不同的作業系統上工作。

#cloudflared tunnel --config config.yml run vkc-tunnel