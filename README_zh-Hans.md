# Anx Calibre Manager

[![Docker Image CI](https://github.com/ptbsare/anx-calibre-manager/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/ptbsare/anx-calibre-manager/actions/workflows/docker-ci.yml)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-ptbsare%2Fanx--calibre--manager-blue?logo=github)](https://github.com/ptbsare/anx-calibre-manager/pkgs/container/anx-calibre-manager)

一个现代化的、移动端优先的 Web 应用，用于管理您的电子书库，可与 Calibre 集成，并为您的 Anx-reader 兼容设备提供个人 WebDAV 服务器。

<p align="center">
  <strong><a href="README.md">English</a></strong> |
  <strong><a href="README_zh-Hans.md">简体中文</a></strong> |
  <strong><a href="README_zh-Hant.md">繁體中文</a></strong> |
  <strong><a href="README_es.md">Español</a></strong> |
  <strong><a href="README_fr.md">Français</a></strong> |
  <strong><a href="README_de.md">Deutsch</a></strong>
</p>

## ✨ 功能特性

- **多语言支持**: 完整的国际化支持，界面提供英语、简体中文 (简体中文)、繁体中文 (繁體中文)、西班牙语、法语和德语。
- **移动端优先界面**: 简洁、响应式的用户界面，专为在手机上轻松使用而设计。
- **PWA 支持**: 可作为渐进式 Web 应用 (PWA) 安装，提供类似原生应用的体验。
- **浏览器内图书预览器**: 直接在浏览器中预览电子书。支持文本转语音（TTS）功能。
- **有声书生成**: 使用可配置的文本转语音（TTS）提供商（例如，Microsoft Edge TTS），将 EPUB 电子书转换为带章节标记的 M4B 有声书。生成的 M4B 文件与 [Audiobookshelf](https://www.audiobookshelf.org/) 等有声书服务器完全兼容。
- **在线有声书播放器**: 直接在浏览器中收听您生成的 M4B 有声书。您的收听进度会被自动保存和同步。
- **与 AI 对话**: 与您的书籍进行对话。此功能允许您与书库中的任何一本书聊天，通过 AI 驱动的界面提出关于内容的问题、获取摘要或探讨主题。
- **Calibre 集成**: 连接到您现有的 Calibre 服务器，以浏览和搜索您的书库。
- **KOReader 同步**: 与您的 KOReader 设备同步阅读进度和阅读时间。
- **智能推送到 Kindle**: 发送书籍到您的 Kindle 时，应用会自动处理格式。如果书籍已有 EPUB 格式，则直接发送；如果没有，它将根据您的格式偏好设置，自动将最优先的可用格式**转换为 EPUB**后再发送，以确保最佳兼容性。
- **推送到 Anx**: 将书籍从您的 Calibre 书库直接发送到您的个人 Anx-reader 设备文件夹。
- **集成的 WebDAV 服务器**: 每个用户都会获得自己独立、安全的 WebDAV 文件夹，与 Anx-reader 和其他 WebDAV 客户端兼容。
- **MCP 服务器**: 内置一个符合规范的 Model Context Protocol (MCP) 服务器，允许 AI 代理和外部工具安全地与您的书库交互。
- **用户管理**: 简单、内置的用户管理系统，具有不同的角色：
    - **管理员 (Admin)**: 对用户、全局设置和所有书籍拥有完全控制权。
    - **维护者 (Maintainer)**: 可以编辑所有书籍元数据。
    - **普通用户 (User)**: 可以上传书籍、管理自己的 WebDAV 书库、MCP token、发送书籍到 Kindle，以及**编辑自己上传的书籍**。
- **安全设计**: 为保护您的 Calibre 书库安全，Anx Calibre Manager 不提供删除 Calibre 书籍的接口。如果您的书库包含成千上万本图书，建议在公网暴露 Anx Calibre Manager 时，通过内网的 Calibre 内容服务器（默认端口 8080）来管理书籍删除操作。
- **仅限邀请注册**: 管理员可以生成邀请码来控制用户注册。此功能默认启用，以防止未经授权的注册。
- **用户可编辑自己上传的书籍**: 普通用户现在可以编辑自己上传的书籍的元数据。此功能依赖于 Calibre 中的一个名为 `#library` 的自定义列（类型：`文本`）。当用户上传书籍时，他们的用户名会自动保存到该字段。用户可以编辑 `#library` 字段中记录的、由自己上传的任何书籍。
    - **Docker 用户建议**: 为启用此功能，请确保您的 Calibre 书库中有一个名为 `#library` 的自定义列（区分大小写），类型为 `文本`。
- **轻松部署**: 可作为单个 Docker 容器进行部署，内置了多语言环境支持。
- **阅读统计**: 自动生成个人阅读统计页面，包含年度阅读热力图、在读书籍和已读书籍列表。页面支持公开或私有分享。
## 📸 截图

<p align="center">
  <em>主界面</em><br>
  <img src="screenshots/Screen Shot - MainPage.png">
</p>
<p align="center">
  <em>设置页面</em><br>
  <img src="screenshots/Screen Shot - SettingPage.png">
</p>

<p align="center">
  <em>MCP 设置</em><br>
  <img src="screenshots/Screen Shot - MCPSetting.png">
</p>

| MCP 聊天 | MCP 聊天 | MCP 聊天 | MCP 聊天 |
| :---: | :---: | :---: | :---: |
| <img src="screenshots/Screen Shot - MCPChat.jpg" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-1.png" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-2.png" width="250"/> | <img src="screenshots/Screen Shot - MCPChat2-3.png" width="250"/> |

| Koreader 书籍状态 | Koreader 同步 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - KoreaderBookStatus.jpg" width="400"/> | <img src="screenshots/Screen Shot - KoreaderSync.jpg" width="400"/> |

| Koreader 设置 | Koreader WebDAV |
| :---: | :---: |
| <img src="screenshots/Screen Shot - KoreaderSetting.png" width="750"/> | <img src="screenshots/Screen Shot - KoreaderWebdav.jpg" width="250"/> |

<p align="center">
  <em>统计页面</em><br>
  <img src="screenshots/Screen Shot - StatsPage.png">
</p>

| 有声书列表 | 有声书播放器 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - AudiobookList.png" width="400"/> | <img src="screenshots/Screen Shot - AudiobookPlayer.png" width="400"/> |

| 与图书对话 | 与图书对话 |
| :---: | :---: |
| <img src="screenshots/Screen Shot - ChatWithBook1.png" width="400"/> | <img src="screenshots/Screen Shot - ChatWithBook2.png" width="400"/> |

## 🚀 部署

本应用设计为使用 Docker 进行部署。

### 先决条件

- 您的服务器上已安装 [Docker](https://www.docker.com/get-started)。
- **Calibre 服务器**（二选一）：
  - **方案一：使用 AIO（一体化）镜像** - 内置 `calibre-server`。适合想要简单、单容器部署的新手用户。
  - **方案二：使用现有的 Calibre 服务器** - 运行单独的 Calibre 服务器 Docker 镜像。推荐使用 [linuxserver/calibre](https://hub.docker.com/r/linuxserver/calibre) 或轻量级的 [lucapisciotta/calibre](https://hub.docker.com/r/lucapisciotta/calibre)（默认端口：`8085`）。

### 快速开始 (使用 Docker Run)

#### AIO 版本 (一体化 - 推荐)
如果您不想管理单独的 Calibre 服务器，这是最佳选择！

1.  创建三个用于持久化数据的文件夹：
    ```bash
    mkdir -p ./config
    mkdir -p ./webdav
    mkdir -p ./library
    ```

2.  运行 AIO Docker 容器：
    ```bash
    docker run -d \
      --name anx-calibre-manager-aio \
      -p 5000:5000 \
      -p 8080:8080 \
      -v $(pwd)/config:/config \
      -v $(pwd)/webdav:/webdav \
      -v $(pwd)/library:"/Calibre Library" \
      -e CALIBRE_URL=http://localhost:8080 \
      -e CALIBRE_USERNAME=admin \
      -e CALIBRE_PASSWORD=password \
      --restart unless-stopped \
      ghcr.io/ptbsare/anx-calibre-manager:aio-latest
    ```

3.  在浏览器中访问 `http://localhost:5000`。内置的 Calibre 服务器将在 `http://localhost:8080` 可用。
    - **注意**：`/Calibre Library` 目录是您的 Calibre 书库文件夹。它将包含 `metadata.db`（Calibre 数据库）、书籍文件和封面图片。这是内置 Calibre 服务器存储和管理所有电子书的地方。
    - **注意**：为了安全起见，请修改默认的用户名（`admin`）和密码（`password`）。

#### 标准版本
适用于已有独立 Calibre 服务器的用户。

1.  创建两个用于持久化数据的文件夹：
    ```bash
    mkdir -p ./config
    mkdir -p ./webdav
    ```

2.  使用下面这一条命令来启动 Docker 容器：
    ```bash
    docker run -d \
      --name anx-calibre-manager \
      -p 5000:5000 \
      -v $(pwd)/config:/config \
      -v $(pwd)/webdav:/webdav \
      --restart unless-stopped \
      ghcr.io/ptbsare/anx-calibre-manager:latest
    ```

3.  在浏览器中访问 `http://localhost:5000`。第一个注册的用户将自动成为管理员。您后续可以在网页界面中配置 Calibre 服务器连接及其他设置。

### 高级配置

对于希望连接到 Calibre 服务器并自定义更多选项的用户，这里提供一个更详细的 `docker-compose.yml` 示例。

1.  **获取您的用户和组 ID (PUID/PGID):**
    在您的宿主机上运行 `id $USER`。为了避免权限问题，建议进行此项配置。

2.  **创建一个 `docker-compose.yml` 文件:**
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
          - /path/to/your/audiobooks:/audiobooks # 可选
          - /path/to/your/fonts:/opt/share/fonts # 可选
        environment:
          - PUID=1000
          - PGID=1000
          - TZ=Asia/Shanghai
          - GUNICORN_WORKERS=2 # 可选
          - SECRET_KEY=your_super_secret_key # 请修改为您的密钥
          - CALIBRE_URL=http://your-calibre-server-ip:8080
          - CALIBRE_USERNAME=your_calibre_username
          - CALIBRE_PASSWORD=your_calibre_password
          - CALIBRE_DEFAULT_LIBRARY_ID=Calibre_Library
          - CALIBRE_ADD_DUPLICATES=false
        restart: unless-stopped
    ```
    *注意: 请将 `/path/to/your/...` 替换为您宿主机上的实际路径。*

3.  启动容器:
    ```bash
    docker-compose up -d
    ```

### 自定义字体

书籍格式转换工具 `ebook-converter` 会扫描 `/opt/share/fonts` 目录以查找字体。如果您在转换某些包含特殊字符（如中文）的书籍时遇到字体问题，可以通过挂载一个包含您所需字体文件（例如 `.ttf`, `.otf`）的本地目录到容器的 `/opt/share/fonts` 路径来提供自定义字体。

### 配置

应用通过环境变量进行配置。

| 变量 | 描述 | 默认值 |
| --- | --- | --- |
| `PUID` | 指定运行应用的用户 ID。 | `1001` |
| `PGID` | 指定运行应用的组 ID。 | `1001` |
| `TZ` | 您的时区, 例如 `America/New_York`。 | `UTC` |
| `PORT` | 应用在容器内监听的端口。 | `5000` |
| `GUNICORN_WORKERS` | 可选：Gunicorn worker 进程的数量。 | `2` |
| `CONFIG_DIR` | 用于存放数据库和 `settings.json` 的目录。 | `/config` |
| `WEBDAV_DIR` | 用于存放 WebDAV 用户文件的基础目录。 | `/webdav` |
| `SECRET_KEY` | **必需。** 用于会话安全的、长的、随机的字符串。 | `""` |
| `LOGIN_MAX_ATTEMPTS` | 登录失败锁定阈值。设为 `0` 禁用此功能。 | `5` |
| `SESSION_LIFETIME_DAYS` | 用户登录后会话保持有效的天数。 | `7` |
| `ENABLE_ACTIVITY_LOG` | 启用用户活动日志记录（登录、下载、上传等操作）到数据库用于审计目的。 | `false` |
| `CALIBRE_URL` | 您的 Calibre 内容服务器的 URL。**在 AIO 版本中具有双重作用**：(1) 作为 anx-calibre-manager 的全局默认 Calibre 服务器连接配置。(2) 从中提取端口号，用于确定内置 calibre-server 应监听的端口。例如，`http://localhost:8080` 将使 calibre-server 监听 8080 端口。如有连接问题，请参阅[问题排查](#1-为什么我的-calibre-列表没有书籍)。 | `""` |
| `CALIBRE_USERNAME` | 您的 Calibre 服务器的用户名。如有连接问题，请参阅[问题排查](#1-为什么我的-calibre-列表没有书籍)。 | `""` |
| `CALIBRE_PASSWORD` | 您的 Calibre 服务器的密码。如有连接问题，请参阅[问题排查](#1-为什么我的-calibre-列表没有书籍)。 | `""` |
| `CALIBRE_DEFAULT_LIBRARY_ID` | 默认的 Calibre 库 ID。详情请参阅[如何找到我的 `library_id`](#4-我如何找到我的-library_id)。 | `Calibre_Library` |
| `CALIBRE_ADD_DUPLICATES` | 是否允许上传重复的书籍。 | `false` |
| `REQUIRE_INVITE_CODE` | 注册时是否需要邀请码。 | `true` |
| `DISABLE_NORMAL_USER_UPLOAD` | 当设置为 `true` 时，禁用"普通用户"角色的书籍上传功能，仅管理员和维护者可上传书籍。 | `false` |
| `SMTP_SERVER` | 用于发送邮件 (例如，推送到 Kindle) 的 SMTP 服务器。 | `""` |
| `SMTP_PORT` | SMTP 端口。 | `587` |
| `SMTP_USERNAME` | SMTP 用户名。 | `""` |
| `SMTP_PASSWORD` | SMTP 密码。 | `""` |
| `SMTP_ENCRYPTION` | SMTP 加密类型 (`ssl`, `starttls`, `none`)。 | `ssl` |
| `DEFAULT_TTS_PROVIDER` | 用于有声书生成的默认 TTS 提供商 (`edge_tts` 或 `openai_tts`)。 | `edge_tts` |
| `DEFAULT_TTS_VOICE` | 所选 TTS 提供商的默认语音。 | `en-US-AriaNeural` |
| `DEFAULT_TTS_RATE` | TTS 提供商的默认语速 (例如, `+10%`)。 | `+0%` |
| `DEFAULT_TTS_SENTENCE_PAUSE` | 句子之间的默认停顿时间（毫秒）。 | `650` |
| `DEFAULT_TTS_PARAGRAPH_PAUSE` | 段落之间的默认停顿时间（毫秒）。 | `900` |
| `DEFAULT_OPENAI_API_KEY` | 您的 OpenAI API 密钥 (如果使用 `openai_tts` 则为必需)。 | `""` |
| `DEFAULT_OPENAI_API_BASE_URL` | 用于 OpenAI 兼容 API 的自定义基础 URL。 | `https://api.openai.com/v1` |
| `DEFAULT_OPENAI_API_MODEL` | 用于 TTS 的 OpenAI 模型 (例如, `tts-1`)。 | `tts-1` |
| `DEFAULT_LLM_BASE_URL` | 大语言模型 (LLM) API 的基础 URL，需与 OpenAI API 格式兼容。 | `""` |
| `DEFAULT_LLM_API_KEY` | LLM 服务的 API 密钥。 | `""` |
| `DEFAULT_LLM_MODEL` | LLM 服务默认使用的模型 (例如, `gpt-4`)。 | `""` |

## 🔧 问题排查

这里是一些常见问题及其解决方案：

### 1. 为什么我的 Calibre 列表没有书籍？

*   **A**: 请确保您已在 Calibre 客户端或容器中启动了 Calibre 内容服务（Content Server），即 `calibre-server`。它通常运行在 `8080` 端口。请注意，本程序连接的是 `calibre-server`，而不是 `calibre-web`（后者通常运行在 `8083` 端口）。
*   **B**: 请确认您在设置中填写的 Calibre 服务器 URL、用户名和密码是正确的。您可以在浏览器中打开您配置的 URL，并尝试使用相同的用户名和密码登录来测试连接。

### 2. 为什么上传/编辑书籍时出现 `401 Unauthorized` 错误？

*   **A**: 请确保您所配置的 Calibre 用户账户对书库具有写入权限。检查方法：在 Calibre 桌面应用中，点击 `首选项` -> `通过网络共享` -> `用户账户`，并确保已为该用户勾选了“授予写入权限”选项。

### 3. 为什么上传/编辑书籍时出现 `403 Forbidden` 错误？

*   **A**: 这通常意味着您配置了错误的 Calibre Library ID。

### 4. 我如何找到我的 `library_id`？

*   **方法一 (可视化)**: 在浏览器中打开您的 Calibre 内容服务并登录。查看页面上显示的书库名称。`library_id` 通常是这个名称将空格等特殊字符替换为下划线后的结果。例如，如果您的书库名为 "Calibre Library"，那么 ID 很可能就是 `Calibre_Library`。
*   **方法二 (从 URL)**: 在内容服务界面，点击您的书库名称。查看浏览器地址栏中的 URL，您应该能看到一个类似 `library_id=...` 的参数。该参数的值就是您的 library ID（它可能经过了 URL 编码，您可能需要解码一下）。
*   **常见的默认 ID**: 首次运行 Calibre 时，默认的书库 ID 通常取决于您的系统语言。以下是一些常见的默认值：
    *   英语: `Calibre_Library`
    *   法语: `Bibliothèque_calibre`
    *   德语: `Calibre-Bibliothek`
    *   西班牙语: `Biblioteca_de_calibre`
    *   简体中文: `Calibre_书库`
    *   繁體中文: `calibre_書庫`

### 5. 为什么在编辑已读日期或书库字段时会出现 `400 Bad Request` 错误？

*   **答**: 此错误表示您的 Calibre 书库缺少存储这些信息所需的自定义列。为了启用跟踪书籍上传者/所有者以及设置特定已读日期的功能，您需要在 Calibre 桌面应用中添加两个自定义列：
    1.  前往 `首选项` -> `添加您自己的列`。
    2.  点击 `添加自定义列`。
    3.  创建第一个列，信息如下：
        *   **查找名称**: `#library`
        *   **列标题**: `Library` (或您喜欢的任何名称)
        *   **列类型**: `文本`
    4.  创建第二个列，信息如下：
        *   **查找名称**: `#readdate`
        *   **列标题**: `Read Date` (或您喜欢的任何名称)
        *   **列类型**: `日期`
    5.  点击 `应用` 并重启您的 Calibre 服务器。添加这些列后，编辑功能即可正常工作。

### 6. 我不想用笨重的 Calibre 客户端或简陋的 calibre-server 来管理书库，能用 Calibre-Web、Calibre-Web-Automated 或 Talebook 等前端吗？

**当然可以！** 您可以在使用本应用的同时，搭配任何兼容 Calibre 的前端程序。这些前端都与同一个 Calibre 书库数据库 (`metadata.db`) 交互，如下图所示：

<p align="center">
  <img src="screenshots/Document -  BookManagerExplained.jpg" alt="Calibre 书库架构">
</p>

**推荐方案：Sidecar 模式 (边车模式)**

将您偏好的前端作为独立容器运行，共享同一个书库目录。这种方式特别适合搭配 **AIO 版本** 使用：

**以 Calibre-Web-Automated 为例：**

使用 Docker Run：
```bash
# 运行 ANX Calibre Manager AIO (内置 calibre-server)
docker run -d \
  --name anx-calibre-manager-aio \
  -p 5000:5000 \
  -p 8080:8080 \
  -v $(pwd)/config:/config \
  -v $(pwd)/webdav:/webdav \
  -v $(pwd)/library:"/Calibre Library" \
  -e CALIBRE_URL=http://localhost:8080 \
  -e CALIBRE_USERNAME=admin \
  -e CALIBRE_PASSWORD=password \
  ghcr.io/ptbsare/anx-calibre-manager:aio-latest

# 运行 Calibre-Web-Automated (共享书库)
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

**要点说明：**
- **共享书库**：将同一个书库目录 (`./library`) 挂载到所有容器
- **无端口冲突**：每个前端运行在独立端口 (ANX: 5000, calibre-server: 8080, CWA: 8083)
- **服务独立**：每个容器可以独立启动/停止
- **适用标准版**：如果您已有独立的 Calibre 服务器，此模式同样适用于标准版 (非 AIO)

## 📖 KOReader 同步

您可以同步您的阅读进度和阅读时间到 Anx 书库。整个设置过程分为两步：首先配置 WebDAV 以便访问您的书籍，然后配置同步插件来处理进度同步。

### 第一步：配置 WebDAV 云存储

此步骤让您可以直接在 KOReader 中浏览和阅读您的 Anx 书库中的书籍。

1.  在 KOReader 中，进入 `云存储` -> `添加新的云存储`。
2.  选择 `WebDAV`。
3.  填写以下详细信息：
    -   **服务器地址**: 填写 Anx Calibre Manager 设置页面（`设置` -> `Koreader 同步设置`）中显示的 WebDAV 地址。**请确保路径以 `/` 结尾**。
    -   **用户名**: 您的 Anx Calibre Manager 用户名。
    -   **密码**: 您的 Anx Calibre Manager 登录密码。
    -   **文件夹**: `/anx/data/file`
4.  点击 `连接` 并保存。现在您应该可以在 KOReader 的文件浏览器中看到您的 Anx 书库了。

### 第二步：安装并配置同步插件

此插件负责将您的阅读进度发送回 Anx Calibre Manager 服务器。

1.  **下载插件**:
    -   登录 Anx Calibre Manager。
    -   进入 `设置` -> `Koreader 同步设置`。
    -   点击 `下载 KOReader 插件 (.zip)` 按钮来获取插件包。
2.  **安装插件**:
    -   解压下载的 `.zip` 文件，您会得到一个名为 `anx-calibre-manager-koreader-plugin.koplugin` 的文件夹。
    -   将这**整个文件夹**复制到您 KOReader 设备的 `koreader/plugins/` 目录下。
3.  **重启 KOReader**: 完全关闭并重新打开 KOReader 应用以加载新插件。
4.  **配置同步服务器**:
    -   **重要提示**: 首先，请通过上一步设置的 WebDAV 打开并开始阅读一本书籍。插件菜单**仅在阅读界面中可见**。
    -   在阅读界面，进入 `工具(扳手图标)` -> `下一页` -> `更多工具` -> `ANX Calibre Manager`。
    -   选择 `自定义同步服务器`。
    -   **自定义同步服务器地址**: 输入 Anx Calibre Manager 设置页面中显示的同步服务器地址 (例如: `http://<your_server_address>/koreader`)。
    -   返回上一级菜单，选择 `登录`，并输入您的 Anx Calibre Manager 用户名和密码。

配置完成后，插件将自动或手动同步您的阅读进度。您可以在插件菜单中调整同步频率等设置。**注意：目前仅支持同步 EPUB 格式书籍的进度。**

## 🤖 MCP 服务器

本应用包含一个符合 JSON-RPC 2.0 规范的 MCP (Model Context Protocol) 服务器，允许外部工具和 AI 代理与您的书库进行交互。

### 使用方法

1.  **生成令牌**: 登录后，进入 **设置 -> MCP 设置** 页面。点击“生成新令牌”来创建一个新的 API 令牌。
2.  **端点 URL**: MCP 服务器的端点是 `http://<your_server_address>/mcp`。
3.  **认证**: 在您的请求 URL 中，通过查询参数附加您的令牌，例如：`http://.../mcp?token=YOUR_TOKEN`。
4.  **发送请求**: 向该端点发送 `POST` 请求，请求体需遵循 JSON-RPC 2.0 格式。

### Prompt 示例

以下是一些自然语言提示的示例，您可以将其用于能够访问这些工具的 AI 代理。代理会智能地调用一个或多个工具来满足您的请求。

- **简单和高级搜索**:
  - > "查找关于 Python 编程的书籍。"
  - > "搜索艾萨克·阿西莫夫在1950年后出版的科幻小说。"

- **书籍管理**:
  - > "最近添加的5本书是哪些？把第一本发送到我的 Kindle。"
  - > "将《沙丘》这本书推送到我的 Anx 阅读器上。"
  - > "将我 Anx 书库中的《三体》上传到 Calibre。"
  - > "为《三体》这本书生成有声书。"
  - > "《三体》的有声书生成状态如何？"

- **内容互动与总结**:
  - > "显示《基地》这本书的目录。"
  - > "获取《基地》的第一章内容并给我一个摘要。"
  - > "根据《基地》中‘心理史学家’这一章，心理史学的主要思想是什么？"
  - > "阅读整本《小王子》，并告诉我狐狸的秘密是什么。"

- **阅读统计与进度**:
  - > "《沙丘》这本书总共有多少字，并列出每个章节的字数。"
  - > "我今年读了多少本书？"
  - > "我在《沙丘》上的阅读进度怎么样了？"
  - > "《Project Hail Mary》的作者是谁？这本书我读了多久了？"

### 可用工具

您可以通过 `tools/list` 方法获取所有可用工具的列表。当前支持的工具包括：

-   **`search_calibre_books`**: 使用 Calibre 强大的搜索语法搜索 Calibre 书库中的书籍。
    -   **参数**: `search_expression` (字符串), `limit` (整数, 可选)。
    -   **示例 (高级搜索)**: 搜索由“人民邮电出版社”出版且评分高于4星的图书。
        ```json
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_calibre_books",
                "arguments": {
                    "search_expression": "publisher:\"人民邮电出版社\" AND rating:>=4",
                    "limit": 10
                }
            },
            "id": "search-request-1"
        }
        ```
-   **`get_recent_books`**: 从指定书库获取最近的书籍。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `limit` (整数, 可选)。
-   **`get_book_details`**: 获取指定书库中某本书的详细信息。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`push_calibre_book_to_anx`**: 将 Calibre 书库中的书籍推送到用户的 Anx 书库。
    -   **参数**: `book_id` (整数)。
-   **`push_anx_book_to_calibre`**: 将用户 Anx 书库中的书籍上传到公共 Calibre 书库。
    -   **参数**: `book_id` (整数)。
-   **`send_calibre_book_to_kindle`**: 将 Calibre 书库中的书籍发送到用户配置的 Kindle 邮箱。
    -   **参数**: `book_id` (整数)。
-   **`get_table_of_contents`**: 获取指定书库中书籍的目录。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`get_chapter_content`**: 获取书籍指定章节的内容。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数), `chapter_number` (整数)。
-   **`get_entire_book_content`**: 获取指定书库中书籍的全部内容。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`get_word_count_statistics`**: 获取书籍的字数统计（总字数和每章字数）。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`generate_audiobook`**: 为 Anx 或 Calibre 书库中的书籍生成有声书。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`get_audiobook_generation_status`**: 通过任务 ID 获取有声书生成任务的状态。
    -   **参数**: `task_id` (字符串)。
-   **`get_audiobook_status_by_book`**: 通过书籍 ID 和书库类型获取指定书籍的最新有声书任务状态。
    -   **参数**: `library_type` (字符串, 'anx' 或 'calibre'), `book_id` (整数)。
-   **`get_user_reading_stats`**: 获取当前用户的阅读统计信息。
    -   **参数**: `time_range` (字符串)。此参数为必需项。可以是 "all", "today", "this_week", "this_month", "this_year", 最近的天数（如 "7", "30"）, 或日期范围 "YYYY-MM-DD:YYYY-MM-DD"。

## 💻 开发

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/ptbsare/anx-calibre-manager.git
    cd anx-calibre-manager
    ```

2.  **创建虚拟环境:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **运行开发服务器:**
    ```bash
    python app.py
    ```
    应用将在 `http://localhost:5000` 上可用。

## 🤝 贡献

欢迎提交贡献、问题和功能请求！请随时查看 [问题页面](https://github.com/ptbsare/anx-calibre-manager/issues)。

## 🙏 致谢

本项目使用了以下优秀的开源项目：

-   [foliate-js](https://github.com/johnfactotum/foliate-js) 提供了强大的电子书预览功能。
-   [ebook-converter](https://github.com/gryf/ebook-converter) 提供了可靠的电子书格式转换功能。

## 📄 许可证

本项目采用 GPLv3 许可证。
