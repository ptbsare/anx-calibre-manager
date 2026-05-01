# Anx Calibre Manager

[![Docker Image CI](https://github.com/ptbsare/anx-calibre-manager/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/ptbsare/anx-calibre-manager/actions/workflows/docker-ci.yml)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-ptbsare%2Fanx--calibre--manager-blue?logo=github)](https://github.com/ptbsare/anx-calibre-manager/pkgs/container/anx-calibre-manager)

一個現代化的、行動端優先的 Web 應用程式，用於管理您的電子書庫，可與 Calibre 整合，並為您的 Anx-reader 相容裝置提供個人 WebDAV 伺服器。

<p align="center">
  <strong><a href="README.md">English</a></strong> |
  <strong><a href="README_zh-Hans.md">简体中文</a></strong> |
  <strong><a href="README_zh-Hant.md">繁體中文</a></strong> |
  <strong><a href="README_es.md">Español</a></strong> |
  <strong><a href="README_fr.md">Français</a></strong> |
  <strong><a href="README_de.md">Deutsch</a></strong>
</p>

## ✨ 功能特性

- **多語言支援**: 完整的國際化支援，介面提供英語、簡體中文 (简体中文)、繁體中文 (繁體中文)、西班牙語、法語和德語。
- **行動端優先介面**: 簡潔、響應式的用戶介面，專為在手機上輕鬆使用而設計。
- **PWA 支援**: 可作為漸進式 Web 應用 (PWA) 安裝，提供類似原生應用的體驗。
- **瀏覽器內圖書預覽器**: 直接在瀏覽器中預覽電子書。支援文字轉語音（TTS）功能。
- **有聲書產生**: 使用可設定的文字轉語音（TTS）提供商（例如，Microsoft Edge TTS），將 EPUB 電子書轉換為帶章節標記的 M4B 有聲書。產生的 M4B 檔案與 [Audiobookshelf](https://www.audiobookshelf.org/) 等有聲書伺服器完全相容。
- **線上收聽有聲書**: 直接在瀏覽器中收聽您生成的 M4B 有聲書。您的收聽進度會被自動儲存和同步。
- **與 AI 對話**: 與您的書籍進行對話。此功能允許您與書庫中的任何一本書聊天，透過 AI 驅動的介面提出關於內容的問題、取得摘要或探討主題。
- **Calibre 整合**: 連接到您現有的 Calibre 伺服器，以瀏覽和搜尋您的書庫。
- **KOReader 同步**: 與您的 KOReader 裝置同步閱讀進度和閱讀時間。
- **智慧推送到 Kindle**: 傳送書籍到您的 Kindle 時，應用程式會自動處理格式。如果書籍已有 EPUB 格式，則直接傳送；如果沒有，它將根據您的格式偏好設定，自動將最優先的可用格式**轉換為 EPUB**後再傳送，以確保最佳相容性。
- **推送到 Anx**: 將書籍從您的 Calibre 書庫直接傳送到您的個人 Anx-reader 裝置資料夾。
- **整合的 WebDAV 伺服器**: 每個使用者都會獲得自己獨立、安全的 WebDAV 資料夾，與 Anx-reader 和其他 WebDAV 用戶端相容。
- **MCP 伺服器**: 內建一個符合規範的 Model Context Protocol (MCP) 伺服器，允許 AI 代理和外部工具安全地與您的書庫互動。
- **使用者管理**: 簡單、內建的使用者管理系統，具有不同的角色：
    - **管理員 (Admin)**: 對使用者、全域設定和所有書籍擁有完全控制權。
    - **維護者 (Maintainer)**: 可以編輯所有書籍元資料。
    - **普通使用者 (User)**: 可以上傳書籍、管理自己的 WebDAV 書庫、MCP token、傳送書籍到 Kindle，以及**編輯自己上傳的書籍**。
- **僅限邀請註冊**: 管理員可以產生邀請碼來控制使用者註冊。此功能預設啟用，以防止未經授權的註冊。
- **使用者可編輯自己上傳的書籍**: 普通使用者現在可以編輯自己上傳的書籍的元資料。此功能依賴於 Calibre 中的一個名為 `#library` 的自訂欄位（類型：`文字`）。當使用者上傳書籍時，他們的使用者名稱會自動儲存到該欄位。使用者可以編輯 `#library` 欄位中記錄的、由自己上傳的任何書籍。
    - **Docker 使用者建議**: 為啟用此功能，請確保您的 Calibre 書庫中有一個名為 `#library` 的自訂欄位（區分大小寫），類型為 `文字`。
- **輕鬆部署**: 可作為單一 Docker 容器進行部署，內建了多語言環境支援。
- **閱讀統計**: 自動產生個人閱讀統計頁面，包含年度閱讀熱力圖、在讀書籍和已讀書籍清單。頁面支援公開或私人分享。

## 📸 截圖

<p align="center">
  <em>主介面</em><br>
  <img src="screenshots/Screen Shot - MainPage.png">
</p>
<p align="center">
  <em>設定頁面</em><br>
  <img src="screenshots/Screen Shot - SettingPage.png">
</p>

<p align="center">
  <em>MCP 設定</em><br>
  <img src="screenshots/Screen Shot - MCPSetting.png">
</p>

| MCP 聊天 | MCP 聊天 | MCP 聊天 | MCP 聊天 |
| :---: | :---: | :---: | :---: |
| <img src="screenshots/Screen Shot - MCPChat.jpg" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-1.png" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-2.png" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-3.png" width="250"/> |

| Koreader 書籍狀態 | Koreader 同步 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - KoreaderBookStatus.jpg" width="400"/> | <img src="screenshots/Screen Shot - KoreaderSync.jpg" width="400"/> |

| Koreader 設定 | Koreader WebDAV |
| :---: | :---: |
| <img src="screenshots/Screen Shot - KoreaderSetting.png" width="750"/> | <img src="screenshots/Screen Shot - KoreaderWebdav.jpg" width="250"/> |

<p align="center">
  <em>統計頁面</em><br>
  <img src="screenshots/Screen Shot - StatsPage.png">
</p>

| 有聲書列表 | 有聲書播放器 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - AudiobookList.png" width="400"/> | <img src="screenshots/Screen Shot - AudiobookPlayer.png" width="400"/> |

| 與圖書對話 | 與圖書對話 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - ChatWithBook1.png" width="400"/> | <img src="screenshots/Screen Shot - ChatWithBook2.png" width="400"/> |

## 🚀 部署

本應用程式設計為使用 Docker 進行部署。

### 先決條件

- 您的伺服器上已安裝 [Docker](https://www.docker.com/get-started)。
- **Calibre 伺服器**（二選一）：
  - **方案一：使用 AIO（一體化）映像** - 內建 `calibre-server`。適合想要簡單、單容器部署的新手使用者。
  - **方案二：使用現有的 Calibre 伺服器** - 運行單獨的 Calibre 伺服器 Docker 映像。推薦使用 [linuxserver/calibre](https://hub.docker.com/r/linuxserver/calibre) 或輕量級的 [lucapisciotta/calibre](https://hub.docker.com/r/lucapisciotta/calibre)（預設埠：`8085`）。

### 快速開始 (使用 Docker Run)

#### AIO 版本 (一體化 - 推薦)
如果您不想管理單獨的 Calibre 伺服器，這是最佳選擇！

1.  建立三個用於持久化資料的資料夾：
    ```bash
    mkdir -p ./config
    mkdir -p ./webdav
    mkdir -p ./library
    ```

2.  執行 AIO Docker 容器：
    ```bash
    docker run -d \
      --name anx-calibre-manager-aio \
      -p 5000:5000 \
      -p 8080:8080 \
      -v $(pwd)/config:/config \
      -v $(pwd)/webdav:/webdav \
      -v "$(pwd)/library:/Calibre Library" \
      -e CALIBRE_URL=http://localhost:8080 \
      -e CALIBRE_USERNAME=admin \
      -e CALIBRE_PASSWORD=password \
      --restart unless-stopped \
      ghcr.io/ptbsare/anx-calibre-manager:aio-latest
    ```

3.  在瀏覽器中存取 `http://localhost:5000`。內建的 Calibre 伺服器將在 `http://localhost:8080` 可用。
    - **注意**：`/Calibre Library` 目錄是您的 Calibre 書庫資料夾。它將包含 `metadata.db`（Calibre 資料庫）、書籍檔案和封面圖片。這是內建 Calibre 伺服器儲存和管理所有電子書的地方。
    - **注意**：為了安全起見，請修改預設的使用者名稱（`admin`）和密碼（`password`）。

#### 標準版本
適用於已有獨立 Calibre 伺服器的使用者。

1.  建立兩個用於持久化資料的資料夾：
    ```bash
    mkdir -p ./config
    mkdir -p ./webdav
    ```

2.  使用下面這一條命令來啟動 Docker 容器：
    ```bash
    docker run -d \
      --name anx-calibre-manager \
      -p 5000:5000 \
      -v $(pwd)/config:/config \
      -v $(pwd)/webdav:/webdav \
      --restart unless-stopped \
      ghcr.io/ptbsare/anx-calibre-manager:latest
    ```

3.  在瀏覽器中存取 `http://localhost:5000`。第一個註冊的使用者將自動成為管理員。您後續可以在網頁介面中設定 Calibre 伺服器連線及其他設定。

### 進階設定

對於希望連接到 Calibre 伺服器並自訂更多選項的使用者，這裡提供一個更詳細的 `docker-compose.yml` 範例。

1.  **取得您的使用者和群組 ID (PUID/PGID):**
    在您的主機上運行 `id $USER`。為了避免權限問題，建議進行此項設定。

2.  **建立一個 `docker-compose.yml` 檔案:**
    ```yaml
    services:
      anx-calibre-manager:
        image: ghcr.io/ptbsare/anx-calibre-manager:latest
        container_name: anx-calibre-manager
        ports:
          - "5000:5000"
        volumes:
          - /path/to/your/config:/config
          - /path/to/your/webdav:/webdav
          - /path/to/your/audiobooks:/audiobooks # 可選
          - /path/to/your/fonts:/opt/share/fonts # 可選
        environment:
          - PUID=1000
          - PGID=1000
          - TZ=Asia/Taipei
          - GUNICORN_WORKERS=2 # 可選
          - SECRET_KEY=your_super_secret_key # 請修改為您的金鑰
          - CALIBRE_URL=http://your-calibre-server-ip:8080
          - CALIBRE_USERNAME=your_calibre_username
          - CALIBRE_PASSWORD=your_calibre_password
          - CALIBRE_DEFAULT_LIBRARY_ID=Calibre_Library
          - CALIBRE_ADD_DUPLICATES=false
        restart: unless-stopped
    ```
    *注意: 請將 `/path/to/your/...` 替換為您主機上的實際路徑。*

3.  啟動容器:
    ```bash
    docker-compose up -d
    ```

### 自訂字型

書籍格式轉換工具 `ebook-converter` 會掃描 `/opt/share/fonts` 目錄以尋找字型。如果您在轉換某些包含特殊字元（如中文）的書籍時遇到字型問題，可以透過掛載一個包含您所需字型檔案（例如 `.ttf`, `.otf`）的本地目錄到容器的 `/opt/share/fonts` 路徑來提供自訂字型。

### 設定

應用程式透過環境變數進行設定。

| 變數 | 描述 | 預設值 |
| --- | --- | --- |
| `PUID` | 指定運行應用的使用者 ID。 | `1001` |
| `PGID` | 指定運行應用的群組 ID。 | `1001` |
| `TZ` | 您的時區, 例如 `Asia/Taipei`。 | `UTC` |
| `PORT` | 應用程式在容器內監聽的埠號。 | `5000` |
| `GUNICORN_WORKERS` | 可選：Gunicorn worker 程序的數量。 | `2` |
| `CONFIG_DIR` | 用於存放資料庫和 `settings.json` 的目錄。 | `/config` |
| `WEBDAV_DIR` | 用於存放 WebDAV 使用者檔案的基礎目錄。 | `/webdav` |
| `SECRET_KEY` | **必需。** 用於會話安全的、長的、隨機的字串。 | `""` |
| `LOGIN_MAX_ATTEMPTS` | 登入失敗鎖定閾值。設為 `0` 停用此功能。 | `5` |
| `SESSION_LIFETIME_DAYS` | 使用者登入後會話保持有效的天數。 | `7` |
| `ENABLE_ACTIVITY_LOG` | 啟用使用者活動日誌記錄（登入、下載、上傳等操作）到資料庫用於稽核目的。 | `false` |
| `CALIBRE_URL` | 您的 Calibre 內容伺服器的 URL。**在 AIO 版本中具有雙重作用**：(1) 作為 anx-calibre-manager 的全域預設 Calibre 伺服器連線設定。(2) 從中提取連接埠號，用於確定內建 calibre-server 應監聽的連接埠。例如，`http://localhost:8080` 將使 calibre-server 監聽 8080 連接埠。如有連線問題，請參閱[問題排查](#1-為什麼我的-calibre-清單沒有書籍)。 | `""` |
| `CALIBRE_USERNAME` | 您的 Calibre 伺服器的使用者名稱。如有連線問題，請參閱[問題排查](#1-為什麼我的-calibre-清單沒有書籍)。 | `""` |
| `CALIBRE_PASSWORD` | 您的 Calibre 伺服器的密碼。如有連線問題，請參閱[問題排查](#1-為什麼我的-calibre-清單沒有書籍)。 | `""` |
| `CALIBRE_DEFAULT_LIBRARY_ID` | 預設的 Calibre 庫 ID。詳情請參閱[如何找到我的 `library_id`](#4-我如何找到我的-library_id)。 | `Calibre_Library` |
| `CALIBRE_ADD_DUPLICATES` | 是否允許上傳重複的書籍。 | `false` |
| `DISABLE_NORMAL_USER_UPLOAD` | 當設定為 `true` 時，禁用「普通使用者」角色的書籍上傳功能，僅管理員和維護者可上傳書籍。 | `false` |
| `REQUIRE_INVITE_CODE` | 註冊時是否需要邀請碼。 | `true` |
| `SMTP_SERVER` | 用於傳送郵件 (例如，推送到 Kindle) 的 SMTP 伺服器。 | `""` |
| `SMTP_PORT` | SMTP 埠號。 | `587` |
| `SMTP_USERNAME` | SMTP 使用者名稱。 | `""` |
| `SMTP_PASSWORD` | SMTP 密碼。 | `""` |
| `SMTP_ENCRYPTION` | SMTP 加密類型 (`ssl`, `starttls`, `none`)。 | `ssl` |
| `DEFAULT_TTS_PROVIDER` | 用於有聲書產生的預設 TTS 提供商 (`edge_tts` 或 `openai_tts`)。 | `edge_tts` |
| `DEFAULT_TTS_VOICE` | 所選 TTS 提供商的預設語音。 | `en-US-AriaNeural` |
| `DEFAULT_TTS_RATE` | TTS 提供商的預設語速 (例如, `+10%`)。 | `+0%` |
| `DEFAULT_TTS_SENTENCE_PAUSE` | 句子之間的預設停頓時間（毫秒）。 | `650` |
| `DEFAULT_TTS_PARAGRAPH_PAUSE` | 段落之間的預設停頓時間（毫秒）。 | `900` |
| `DEFAULT_OPENAI_API_KEY` | 您的 OpenAI API 金鑰 (如果使用 `openai_tts` 則為必需)。 | `""` |
| `DEFAULT_OPENAI_API_BASE_URL` | 用於 OpenAI 相容 API 的自訂基礎 URL。 | `https://api.openai.com/v1` |
| `DEFAULT_OPENAI_API_MODEL` | 用於 TTS 的 OpenAI 模型 (例如, `tts-1`)。 | `tts-1` |
| `DEFAULT_LLM_BASE_URL` | 大型語言模型 (LLM) API 的基礎 URL，需與 OpenAI API 格式相容。 | `""` |
| `DEFAULT_LLM_API_KEY` | LLM 服務的 API 金鑰。 | `""` |
| `DEFAULT_LLM_MODEL` | LLM 服務預設使用的模型 (例如, `gpt-4`)。 | `""` |

## 🔧 問題排查

這裡是一些常見問題及其解決方案：

### 1. 為什麼我的 Calibre 清單沒有書籍？

*   **A**: 請確保您已在 Calibre 用戶端或容器中啟動了 Calibre 內容服務（Content Server），即 `calibre-server`。它通常運行在 `8080` 連接埠。請注意，本程式連接的是 `calibre-server`，而不是 `calibre-web`（後者通常運行在 `8083` 連接埠）。
*   **B**: 請確認您在設定中填寫的 Calibre 伺服器 URL、使用者名稱和密碼是正確的。您可以在瀏覽器中開啟您設定的 URL，並嘗試使用相同的使用者名稱和密碼登入來測試連線。

### 2. 為什麼上傳/編輯書籍時出現 `401 Unauthorized` 錯誤？

*   **A**: 請確保您所設定的 Calibre 使用者帳戶對書庫具有寫入權限。檢查方法：在 Calibre 桌面應用程式中，點擊 `偏好設定` -> `透過網路分享` -> `使用者帳戶`，並確保已為該使用者勾選了「授予寫入權限」選項。

### 3. 為什麼上傳/編輯書籍時出現 `403 Forbidden` 錯誤？

*   **A**: 這通常意味著您設定了錯誤的 Calibre Library ID。

### 4. 我如何找到我的 `library_id`？

*   **方法一 (視覺化)**: 在瀏覽器中開啟您的 Calibre 內容服務並登入。查看頁面上顯示的書庫名稱。`library_id` 通常是這個名稱將空格等特殊字元替換為底線後的結果。例如，如果您的書庫名為 "Calibre Library"，那麼 ID 很可能就是 `Calibre_Library`。
*   **方法二 (從 URL)**: 在內容服務介面，點擊您的書庫名稱。查看瀏覽器網址列中的 URL，您應該能看到一個類似 `library_id=...` 的參數。該參數的值就是您的 library ID（它可能經過了 URL 編碼，您可能需要解碼一下）。
*   **常見的預設 ID**: 首次運行 Calibre 時，預設的書庫 ID 通常取決於您的系統語言。以下是一些常見的預設值：
    *   英語: `Calibre_Library`
    *   法語: `Bibliothèque_calibre`
    *   德語: `Calibre-Bibliothek`
    *   西班牙語: `Biblioteca_de_calibre`
    *   簡體中文: `Calibre_书库`
    *   繁體中文: `calibre_書庫`

### 5. 為什麼在編輯已讀日期或書庫欄位時會出現 `400 Bad Request` 錯誤？

*   **答**: 此錯誤表示您的 Calibre 書庫缺少儲存這些資訊所需的自訂欄位。為了啟用追蹤書籍上傳者/擁有者以及設定特定已讀日期的功能，您需要在 Calibre 桌面應用程式中新增兩個自訂欄位：
    1.  前往 `偏好設定` -> `新增您自己的欄位`。
    2.  點擊 `新增自訂欄位`。
    3.  建立第一個欄位，資訊如下：
        *   **查詢名稱**: `#library`
        *   **欄位標題**: `Library` (或您喜歡的任何名稱)
        *   **欄位類型**: `文字`
    4.  建立第二個欄位，資訊如下：
        *   **查詢名稱**: `#readdate`
        *   **欄位標題**: `Read Date` (或您喜歡的任何名稱)
        *   **欄位類型**: `日期`
    5.  點擊 `套用` 並重新啟動您的 Calibre 伺服器。新增這些欄位後，編輯功能即可正常運作。

### 6. 為什麼左側 Calibre 書庫沒有刪除書籍的按鈕？

**這是刻意設計的安全特性。** 當 Anx Calibre Manager 暴露在公用網路時，為了防止誤操作或惡意刪除您書庫中的書籍（特別是擁有成千上萬本圖書的書庫），我們沒有提供刪除 Calibre 書籍的介面。

**如需刪除 Calibre 書籍，請使用以下方式：**
- 透過內網存取 Calibre 內容伺服器（預設通訊埠 `8080`）進行刪除操作
- 或使用 Calibre 桌面客戶端進行管理

這樣可以確保您的書庫在享受 Anx Calibre Manager 便利功能的同時，不會因暴露在公網上而面臨資料遺失的風險。

### 7. 我不想使用笨重的 Calibre 桌面用戶端或基本的 calibre-server 來管理我的書庫。我可以使用 Calibre-Web、Calibre-Web-Automated 或 Talebook 等其他前端嗎？

**當然可以！** 您可以將任何 Calibre 相容的前端與本應用程式一起使用。這些前端都與相同的 Calibre 書庫資料庫 (`metadata.db`) 互動，如下圖所示：
  <img src="screenshots/Document%20-%20BookManagerExplained.jpg" alt="Calibre 書庫架構">
</p>

**推薦方法：Sidecar(邊車)模式**

將您偏好的前端作為單獨的容器運行，共享相同的書庫目錄。這種方式特別適合與 **AIO 版本**配合使用：

**與 Calibre-Web-Automated 搭配使用的範例：**

使用 Docker Run：
```bash
# 執行 ANX Calibre Manager AIO（包含 calibre-server）
docker run -d \
  --name anx-calibre-manager-aio \
  -p 5000:5000 \
  -p 8080:8080 \
  -v $(pwd)/config:/config \
  -v $(pwd)/webdav:/webdav \
  -v "$(pwd)/library:/Calibre Library" \
  -e CALIBRE_URL=http://localhost:8080 \
  -e CALIBRE_USERNAME=admin \
  -e CALIBRE_PASSWORD=password \
  ghcr.io/ptbsare/anx-calibre-manager:aio-latest

# 執行 Calibre-Web-Automated（共享書庫）
docker run -d \
  --name calibre-web-automated \
  -p 8083:8083 \
  -v $(pwd)/library:/calibre-library:rw \
  -v $(pwd)/cwa-config:/config \
  -e PUID=1000 \
  -e PGID=1000 \
  ghcr.io/crocodilestick/calibre-web-automated:latest
```

使用 Docker Compose：
```yaml
services:
  anx-calibre-manager-aio:
    image: ghcr.io/ptbsare/anx-calibre-manager:aio-latest
    container_name: anx-calibre-manager-aio
    ports:
      - "5000:5000"
      - "8080:8080"
    volumes:
      - ./config:/config
      - ./webdav:/webdav
      - "./library:/Calibre Library"
    environment:
      - CALIBRE_URL=http://localhost:8080
      - CALIBRE_USERNAME=admin
      - CALIBRE_PASSWORD=password
    restart: unless-stopped

  calibre-web-automated:
    image: ghcr.io/crocodilestick/calibre-web-automated:latest
    container_name: calibre-web-automated
    ports:
      - "8083:8083"
    volumes:
      - ./library:/calibre-library:rw
      - ./cwa-config:/config
    environment:
      - PUID=1000
      - PGID=1000
    restart: unless-stopped
```

**重點提示：**
- **共享書庫**：將相同的書庫目錄（`./library`）掛載到所有容器
- **無衝突**：每個前端在自己的連接埠上運行（ANX：5000，calibre-server：8080，CWA：8083）
- **獨立服務**：每個容器可以獨立啟動/停止
- **適用於標準版本**：如果您已有單獨的 Calibre 伺服器，也可以將此模式用於標準版（非 AIO）

## 📖 KOReader 同步

您可以同步您的閱讀進度和閱讀時間到 Anx 書庫。整個設定過程分為兩步：首先設定 WebDAV 以便存取您的書籍，然後設定同步外掛程式來處理進度同步。

### 第一步：設定 WebDAV 雲端儲存

此步驟讓您可以直接在 KOReader 中瀏覽和閱讀您的 Anx 書庫中的書籍。

1.  在 KOReader 中，進入 `雲端儲存` -> `新增雲端儲存`。
2.  選擇 `WebDAV`。
3.  填寫以下詳細資訊：
    -   **伺服器位址**: 填寫 Anx Calibre Manager 設定頁面（`設定` -> `Koreader 同步設定`）中顯示的 WebDAV 位址。**請確保路徑以 `/` 結尾**。
    -   **使用者名稱**: 您的 Anx Calibre Manager 使用者名稱。
    -   **密碼**: 您的 Anx Calibre Manager 登入密碼。
    -   **資料夾**: `/anx/data/file`
4.  點擊 `連線` 並儲存。現在您應該可以在 KOReader 的檔案瀏覽器中看到您的 Anx 書庫了。

### 第二步：安裝並設定同步外掛程式

此外掛程式負責將您的閱讀進度傳送回 Anx Calibre Manager 伺服器。

1.  **下載外掛程式**:
    -   登入 Anx Calibre Manager。
    -   進入 `設定` -> `Koreader 同步設定`。
    -   點擊 `下載 KOReader 外掛程式 (.zip)` 按鈕來取得外掛程式包。
2.  **安裝外掛程式**:
    -   解壓縮下載的 `.zip` 檔案，您會得到一個名為 `anx-calibre-manager-koreader-plugin.koplugin` 的資料夾。
    -   將這**整個資料夾**複製到您 KOReader 裝置的 `koreader/plugins/` 目錄下。
3.  **重新啟動 KOReader**: 完全關閉並重新開啟 KOReader 應用程式以載入新外掛程式。
4.  **設定同步伺服器**:
    -   **重要提示**: 首先，請透過上一步設定的 WebDAV 開啟並開始閱讀一本書籍。外掛程式選單**僅在閱讀介面中可見**。
    -   在閱讀介面，進入 `工具(扳手圖示)` -> `下一頁` -> `更多工具` -> `ANX Calibre Manager`。
    -   選擇 `自訂同步伺服器`。
    -   **自訂同步伺服器位址**: 輸入 Anx Calibre Manager 設定頁面中顯示的同步伺服器位址 (例如: `http://<your_server_address>/koreader`)。
    -   返回上一層選單，選擇 `登入`，並輸入您的 Anx Calibre Manager 使用者名稱和密碼。

設定完成後，外掛程式將自動或手動同步您的閱讀進度。您可以在外掛程式選單中調整同步頻率等設定。**注意：目前僅支援同步 EPUB 格式書籍的進度。**

## 🤖 MCP 伺服器

本應用程式包含一個符合 JSON-RPC 2.0 規範的 MCP (Model Context Protocol) 伺服器，允許外部工具和 AI 代理與您的書庫進行互動。

### 使用方法

1.  **產生權杖**: 登入後，進入 **設定 -> MCP 設定** 頁面。點擊「產生新權杖」來建立一個新的 API 權杖。
2.  **端點 URL**: MCP 伺服器的端點是 `http://<your_server_address>/mcp`。
3.  **認證**: 在您的請求 URL 中，透過查詢參數附加您的權杖，例如：`http://.../mcp?token=YOUR_TOKEN`。
4.  **傳送請求**: 向該端點傳送 `POST` 請求，請求體需遵循 JSON-RPC 2.0 格式。

### Prompt 範例

以下是一些自然語言提示的範例，您可以將其用於能夠存取這些工具的 AI 代理。代理會智慧地呼叫一個或多個工具來滿足您的請求。

- **簡單和進階搜尋**:
  - > "尋找關於 Python 程式設計的書籍。"
  - > "搜尋艾薩克·アシモフ在1950年後出版的科幻小說。"

- **書籍管理**:
  - > "最近新增的5本書是哪些？把第一本傳送到我的 Kindle。"
  - > "將《沙丘》這本書推送到我的 Anx 閱讀器上。"
  - > "將我 Anx 書庫中的《三體》上傳到 Calibre。"
  - > "為《三體》這本書產生有聲書。"
  - > "《三體》的有聲書產生狀態如何？"

- **內容互動與摘要**:
  - > "顯示《基地》這本書的目錄。"
  - > "取得《基地》的第一章內容並給我一個摘要。"
  - > "根據《基地》中‘心理史學家’這一章，心理史學的主要思想是什麼？"
  - > "閱讀整本《小王子》，並告訴我狐狸的秘密是什麼。"

- **閱讀統計與進度**:
  - > "《沙丘》這本書總共有多少字，並列出每個章節的字數。"
  - > "我今年讀了多少本書？"
  - > "我在《沙丘》上的閱讀進度怎麼樣了？"
  - > "《Project Hail Mary》的作者是誰？這本書我讀了多久了？"

### 可用工具

您可以透過 `tools/list` 方法取得所有可用工具的清單。目前支援的工具包括：

-   **`search_calibre_books`**: 使用 Calibre 強大的搜尋語法搜尋 Calibre 書庫中的書籍。
    -   **參數**: `search_expression` (字串), `limit` (整數, 可選)。
    -   **範例 (進階搜尋)**: 搜尋由「O'Reilly Media」出版且評分高於4星的圖書。
        ```json
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_calibre_books",
                "arguments": {
                    "search_expression": "publisher:\"O'Reilly Media\" AND rating:>=4",
                    "limit": 10
                }
            },
            "id": "search-request-1"
        }
        ```
-   **`get_recent_books`**: 從指定書庫取得最近的書籍。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `limit` (整數, 可選)。
-   **`get_book_details`**: 取得指定書庫中某本書的詳細資訊。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`push_calibre_book_to_anx`**: 將 Calibre 書庫中的書籍推送到使用者的 Anx 書庫。
    -   **參數**: `book_id` (整數)。
-   **`push_anx_book_to_calibre`**: 將使用者 Anx 書庫中的書籍上傳到公共 Calibre 書庫。
    -   **參數**: `book_id` (整數)。
-   **`send_calibre_book_to_kindle`**: 將 Calibre 書庫中的書籍傳送到使用者設定的 Kindle 電子郵件。
    -   **參數**: `book_id` (整數)。
-   **`get_table_of_contents`**: 取得指定書庫中書籍的目錄。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`get_chapter_content`**: 取得書籍指定章節的內容。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數), `chapter_number` (整數)。
-   **`get_entire_book_content`**: 取得指定書庫中書籍的全部內容。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`get_word_count_statistics`**: 取得書籍的字數統計（總字數和每章字數）。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`generate_audiobook`**: 為 Anx 或 Calibre 書庫中的書籍產生有聲書。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`get_audiobook_generation_status`**: 透過任務 ID 獲取有聲書產生任務的狀態。
    -   **參數**: `task_id` (字串)。
-   **`get_audiobook_status_by_book`**: 透過書籍 ID 和書庫類型獲取指定書籍的最新有聲書任務狀態。
    -   **參數**: `library_type` (字串, 'anx' 或 'calibre'), `book_id` (整數)。
-   **`get_user_reading_stats`**: 獲取當前使用者的閱讀統計資訊。
    -   **參數**: `time_range` (字串)。此參數為必需項。可以是 "all", "today", "this_week", "this_month", "this_year", 最近的天數（如 "7", "30"）, 或日期範圍 "YYYY-MM-DD:YYYY-MM-DD"。

## 💻 開發

1.  **克隆儲存庫:**
    ```bash
    git clone https://github.com/ptbsare/anx-calibre-manager.git
    cd anx-calibre-manager
    ```

2.  **建立虛擬環境:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **安裝依賴:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **運行開發伺服器:**
    ```bash
    python app.py
    ```
    應用程式將在 `http://localhost:5000` 上可用。

## 🤝 貢獻

歡迎提交貢獻、問題和功能請求！請隨時查看 [問題頁面](https://github.com/ptbsare/anx-calibre-manager/issues)。

## 🙏 致謝

本專案使用了以下優秀的開源專案：

-   [foliate-js](https://github.com/johnfactotum/foliate-js) 提供了強大的電子書預覽功能。
-   [ebook-converter](https://github.com/gryf/ebook-converter) 提供了可靠的電子書格式轉換功能。

## 📄 授權

本專案採用 GPLv3 授權。