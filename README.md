# QQNT 聊天记录导出工具 (ARK-1)

一个面向 Windows 桌面的 QQNT 聊天记录导出与可视化工具。

`server.py` 既能作为 **Web UI 服务器** 启动（默认行为），也能作为 **交互式 CLI** 或 **无界面批处理 CLI** 运行。Web UI 端通过 WebSocket 与 HTTP 提供完整的聊天预览、消息解码、群成员/精华/通知导出、API 文档与 JSON/CSV 高级导出能力；CLI 端则覆盖同样的功能并支持二次集成。

- **SQLCipher 直接解密**：内置 `--sqlcipher` / 启动时选择，自动通过本地 `sqlcipher.exe` + `sqlite3.exe` 管道将 `*.clean.db` 解密为 `*.decrypt.db`，无需 SQLiteStudio 也不必手写 `tail`。
- **Web UI 控制面板**：基于 `aiohttp` + `websockets` 的三栏布局（好友/群聊列表 + 聊天记录预览 + 实时配置），消息体中的图片、文件、语音、视频、红包、撤回、戳一戳、回复、灰字提示、ARK 卡片都能正确渲染。
- **群信息深整合**：自动加载 `group_info.db`，支持群名片精准显示、成员导出、群精华、群公告、群通知四大附加导出。
- **多格式导出**：`md` / `txt` / `html`（含可切换模板）/ `json` / `csv`，并支持 `json-custom` / `csv-custom` 自定义字段。
- **离线 API 文档**：内置 `/api-docs` 页面，可直接通过 `GET /api?command=...` 触发查询与导出。
- **单文件打包**：通过 `build.spec` 打包成 `.exe`，可与 3 个解密后的数据库同目录双击运行。

---

## 目录

- [快速开始](#快速开始)
- [一、准备工作：解密 QQNT 数据库](#一准备工作解密-qqnt-数据库)
- [二、放置数据库文件](#二放置数据库文件)
- [三、运行程序](#三运行程序)
  - [3.1 Web UI 模式（默认）](#31-web-ui-模式默认)
  - [3.2 交互式 CLI 模式](#32-交互式-cli-模式)
  - [3.3 无界面 CLI 模式](#33-无界面-cli-模式)
- [四、CLI 参数速查](#四cli-参数速查)
- [五、Web API 一览](#五web-api-一览)
- [六、导出格式与配置](#六导出格式与配置)
- [七、目录结构](#七目录结构)
- [八、构建可执行文件](#八构建可执行文件)
- [九、技术参考](#九技术参考)
- [十、常见问题](#十常见问题)
- [十一、免责声明](#十一免责声明)

---

## 快速开始

```powershell
# 1. 解密 QQNT 数据库（详见下一节），得到以下三个文件
nt_msg.decrypt.db
profile_info.decrypt.db
group_info.decrypt.db

# 2. 将它们放在 ark-v9-sqlcipher解密支持.exe 同目录（或源码运行的根目录）

# 3. 双击 .exe，或在源码环境执行：
python server.py

# 浏览器会自动打开 http://localhost:9060
```

如果你的原始数据库是 `*.clean.db`（未解密），只要在同目录放入 `sqlcipher.exe`、`sqlite3.exe`、`decrypt.config`，再执行：

```powershell
python server.py --sqlcipher
```

即可在原地生成 `*.decrypt.db`，随后正常进入 Web UI。

---

## 一、准备工作：解密 QQNT 数据库

`nt_msg.db` / `profile_info.db` / `group_info.db` 在 QQNT 中默认使用 SQLCipher 加密。本仓库支持三条解密路径：从 0 复现上游的 SQLiteStudio 流程、Python 切割 1024 字节头、或直接用本工具自带的 `--sqlcipher` 管道解密。

### 1.0 获取 `pass key`（所有路径都需要）

QQNT 加密参数依赖设备本地的 `nt_uid` 与 `rand`，需要按官方教程计算 `QQ_path_hash` 和最终的 `pass key`：

- 解密教程与在线计算器：[docs.aaqwq.top](https://docs.aaqwq.top/)
- 仓库参考：[QQBackup/qq-win-db-key](https://github.com/QQBackup/qq-win-db-key)

记录下你得到的 `pass key`，后文 `PRAGMA key` 中的 `'user-key'` 占位符都需替换为它。

### 1.1 去掉 `nt_msg.db` 的前 1024 字节

QQNT 的 `nt_msg.db` 在 SQLCipher 密文前还附加了 1024 字节的私有头，解密前必须先剔除。三种等价方法，任选其一：

- **二进制编辑器**：在 Windows 上用 HxD 等工具打开 `nt_msg.db`，选中并删除前 1024 字节，另存为 `nt_msg.clean.db`。
- **Linux `tail` 命令**：

  ```bash
  tail -c +1025 nt_msg.db > nt_msg.clean.db
  ```

- **Python 一行命令**：

  ```bash
  python -c "open('nt_msg.clean.db','wb').write(open('nt_msg.db','rb').read()[1024:])"
  ```

> 完成后会得到 `nt_msg.clean.db`。`profile_info.db` / `group_info.db` 不需要做这步切割。

### 1.2 使用本工具自动解密（推荐）

在工作目录放入：

- `nt_msg.clean.db`
- `profile_info.clean.db`
- `group_info.clean.db`
- `sqlcipher.exe`
- `sqlite3.exe`
- `decrypt.config`

`decrypt.config` 是 SQLCipher 的 PRAGMA 集合，参考内容（`'user-key'` 替换为你从 [docs.aaqwq.top](https://docs.aaqwq.top/) 算出的密钥）：

```text
PRAGMA key = 'user-key';
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 4000;
PRAGMA cipher_hmac_algorithm = HMAC_SHA1;
PRAGMA cipher_default_kdf_algorithm = PBKDF2_HMAC_SHA512;
PRAGMA cipher = 'aes-256-cbc';
```

启动方式：

```powershell
# 强制解密并覆盖
python server.py --sqlcipher --overwrite

# 或双击运行后，在交互式选择中输入 2
```

程序会通过管道把解密结果写入 `*.decrypt.db`：

```text
sqlcipher.exe <db> "<合并后的pragma>" .d  |  sqlite3.exe <db>.decrypt.db
```

### 1.3 手动解密（SQLiteStudio 导出 + sqlite3 重建）

如果你已经熟悉 SQLiteStudio 流程，可以按上游文档操作：

1. 在 SQLiteStudio 中打开 `nt_msg.clean.db`，新建连接并填写以下参数：

   ```text
   PRAGMA key = 'user-key';
   PRAGMA cipher_page_size = 4096;
   PRAGMA kdf_iter = 4000;
   PRAGMA cipher_hmac_algorithm = HMAC_SHA1;
   PRAGMA cipher_default_kdf_algorithm = PBKDF2_HMAC_SHA512;
   PRAGMA cipher = 'aes-256-cbc';
   ```

2. 验证可读后，将整库导出为 SQL 命令文件（例如 `nt_msg.sql`）。
3. 从 [SQLite 官网](https://www.sqlite.org/download.html) 下载 `sqlite3` 命令行工具，加入系统 `PATH`。
4. 执行重建：

   ```powershell
   sqlite3 nt_msg.decrypt.db ".read nt_msg.sql"
   ```

   `profile_info.db` / `group_info.db` 走同样的流程。

> 该流程是简单粗暴做法，需要 SQLiteStudio 配合；本工具的 `--sqlcipher` 等价于此流程但完全命令行化。

> 不论走哪条路径，最终在 Web UI 启动前都需要在工作目录准备好 `*.decrypt.db` 三个文件。

---

## 二、放置数据库文件

将以下三个文件放在 **工作目录** 下（默认即 `.exe` 或 `server.py` 所在目录）：

| 文件 | 是否必需 | 说明 |
| --- | --- | --- |
| `nt_msg.decrypt.db` | 是 | 私聊 + 群聊消息体 |
| `profile_info.decrypt.db` | 是 | 自身 UID、好友、QQ 智能体等个人信息 |
| `group_info.decrypt.db` | 否 | 群成员、群公告、群精华、群通知；缺失时仅降级相关功能 |

---

## 三、运行程序

### 3.1 Web UI 模式（默认）

```powershell
python server.py
# 或双击 ark-v9-sqlcipher解密支持.exe
```

启动成功后控制台会打印：

```text
WebSocket服务器已启动, 监听: ws://localhost:8765
HTTP服务器已启动, 请在浏览器中打开: http://localhost:9060
Web API 文档与测试器: http://localhost:9060/api-docs
```

随后浏览器自动打开三栏控制面板：

- **左栏**：好友 / 群聊列表，按 `ProfileManager` 加载的分组显示。
- **中栏**：聊天记录预览，支持翻页、跳转、消息解码（图片/文件/视频/语音/红包/戳一戳/灰字提示/ARK 卡片/回复）。
- **右栏**：导出配置（消息显示开关、HTML 模板、命名格式等），保存后实时生效。

`/ark-invest` 是同目录提供的另一个分析器页面；`/api-docs` 是 API 文档与在线测试器。

### 3.2 交互式 CLI 模式

```powershell
python server.py --cli
```

进入 `CommandLineInterface`，常用命令：

| 命令 | 说明 |
| --- | --- |
| `help` | 显示所有命令 |
| `list friends` | 列出所有好友（按分组） |
| `list groups` | 列出所有群聊 |
| `list schema` | 列出所有数据库的表与字段 |
| `list fields [c2c|group]` | 列出可导出字段（默认 all） |
| `decrypt [--overwrite]` | 重新执行 SQLCipher 解密 |
| `export <args>` | 触发标准聊天记录导出（参数同命令行 `--mode` 等） |
| `export_extra --group <id> --type <members|essences|notifications|bulletins>` | 群组附加数据导出 |
| `export_raw --db <db> --table <t> --columns <c1,c2>` | 数据库原始列导出 |
| `config <key> <value>` | 修改 `export_config.json` 中的配置项 |
| `set workdir <path>` | 切换数据库所在目录（自动重载） |
| `set outputdir <path>` | 切换导出根目录 |
| `webui` | 启动 Web UI（已启动会提示端口占用） |
| `exit` | 退出 CLI |

### 3.3 无界面 CLI 模式

直接传导出参数即可批量跑任务，常用组合：

```powershell
# 列出全部好友
python server.py --list-friends

# 列出全部群聊
python server.py --list-groups

# 导出所有私聊为 markdown
python server.py --mode individual --friends all --format md

# 导出指定群聊（按群号）时间线合并 html
python server.py --mode timeline --groups 123456789 --format html

# 群成员 / 精华 / 通知 / 公告 导出
python server.py --export-extra --group 123456789 --type members
python server.py --export-extra --group 123456789 --type essences
python server.py --export-extra --group 123456789 --type notifications
python server.py --export-extra --group 123456789 --type bulletins

# 原始列导出（json / csv）
python server.py --export-raw --db nt_msg.decrypt.db --table c2c_msg_table ^
  --columns 40020,40050,40800 --raw-format json

# 指定输出位置
python server.py --mode timeline --friends all --groups all --format html --location D:\backup\qq
```

---

## 四、CLI 参数速查

```
运行模式
  --cli                启动交互式 CLI，不启动 Web UI
  --sqlcipher          启动时强制执行 SQLCipher 解密流程
  --overwrite          与 --sqlcipher 配合，强制覆盖已存在的 .decrypt.db
  --no-browser         启动 Web UI 但不自动打开浏览器
  --log                启用调试模式（控制台显示 WebSocket + 写 DEBUG 日志）

列表与信息
  --list-friends       列出所有好友后退出
  --list-groups        列出所有群聊后退出
  --list-schema        列出数据库表与字段结构后退出
  --list-fields [c2c|group]   列出可导出字段后退出

标准聊天记录导出
  --mode {individual,timeline}
  --friends <uid|qq|"all">    逗号分隔
  --groups  <uin|uid|"all">   逗号分隔
  --format {md,txt,html,json-custom,csv-custom}   默认 md
  --start  'YYYY-MM-DD' | 'YYYY-MM-DD HH:MM:SS'
  --end    'YYYY-MM-DD' | 'YYYY-MM-DD HH:MM:SS'
  --custom-fields <c1,c2,...>      使用 json-custom / csv-custom 时必填
  --group-dirs                     按好友分组分子目录（仅 individual 模式）

高级数据导出
  --export-extra
  --group <id>
  --type   {members,essences,notifications,bulletins}
  --export-raw
  --db <db 文件名>
  --table <表名>
  --columns <c1,c2,...>
  --raw-format {json,csv}
  --parse-pb            尝试解析 Protobuf 二进制字段

Web 服务器与通用配置
  --host         默认 localhost
  --ws_port      默认 8765
  --http_port    默认 9060
  --workdir      数据库所在目录，默认 .
  --location     覆盖默认的根导出目录
```

---

## 五、Web API 一览

Web UI 启动后即可访问 `http://localhost:9060/api-docs`，所有接口都是 `GET /api?command=...`：

| 命令 | 作用 |
| --- | --- |
| `list_friends` | 好友列表（含备注、QQ、UID、分组） |
| `list_groups` | 群聊列表（含群号、UID、当前成员数） |
| `list_db_schema` | 所有数据库的表与字段 |
| `list_fields` | 可导出字段清单 |
| `get_db_info` | 当前 profile / 数据库连接状态 |
| `get_chat_history` | 拉取单条会话的历史消息（支持分页、跳转） |
| `export` | 触发标准导出，返回文件清单与日志 |
| `export_extra` | 触发群组附加数据导出 |
| `export_raw` | 触发数据库原始列导出 |
| `get_config` / `save_config` | 读取 / 保存 `export_config.json` |

WebSocket 协议使用 JSON 消息，命令字段为 `command`，负载字段为 `data / params`，实时进度通过 `type: export_status / export_complete / export_error` 推回客户端。

---

## 六、导出格式与配置

`export_config.json` 与 Web UI 右侧面板共用同一份配置，常用字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `show_recall` | bool | 是否显示撤回消息 |
| `show_recall_suffix` | bool | 是否在撤回消息末尾追加「撤回者」标注 |
| `show_poke` | bool | 是否显示戳一戳 / 互动表情 |
| `show_voice_to_text` | bool | 语音消息是否附带转写文本 |
| `export_non_friends` | bool | 临时会话（陌生人）是否纳入导出 |
| `export_format` | str | `md` / `txt` / `html` / `json-custom` / `csv-custom` |
| `html_template` | str | `html_templates/` 下的模板文件名，默认 `default.html` |
| `show_media_info` | bool | 是否在导出文本中追加「图片 1920x1080」等元信息 |
| `name_style` | str | `default` / `qq` / `uid` / 自定义格式 |
| `name_format` | str | 自定义显示模板，例如 `{remark}({nickname})` |
| `add_file_header` | bool | 是否在每个文件顶部加一段导出元信息 |
| `parse_protobuf_fields` | bool | 是否尝试解析 Protobuf 二进制字段 |
| `api_export_action` | str | API 触发的导出默认 `download` 或 `save` |

修改后通过 Web UI 「保存配置」或 CLI `config <key> <value>` 即时生效；配置文件默认存放在工作目录根。

HTML 模板放在 `html_templates/` 下，可自由扩展后通过 `html_template` 字段切换：

- `default.html`
- `default-v1.html` / `default-v2.html` / `default-v3.html`
- `典雅书卷.html`

---

## 七、目录结构

```text
QQNT聊天记录数据库导出-v9-sqlcipher解密支持/
├── server.py                 # 主程序：Web UI / CLI / API
├── index.html                # Web UI 控制面板
├── api_docs.html             # API 文档与测试器
├── ark-invest.html           # 聊天记录分析器
├── export_config.json        # 默认导出配置
├── decrypt.config            # SQLCipher PRAGMA 集合
├── build.spec                # PyInstaller 配置
├── run.bat                   # 一键启动脚本
├── html_templates/           # HTML 模板
├── lib/                      # 字体/图标/前端依赖
├── log/                      # 运行日志（按 arklog-YYYYMMDD-HHMMSS.log 命名）
├── *.decrypt.db              # 用户提供的解密后数据库（运行时）
├── sqlcipher.exe / sqlite3.exe
└── ark-v9-sqlcipher解密支持.exe  # 打包后的可执行文件
```

日志文件统一存放在 `log/`，启动时打印当前日志路径便于排错。`--log` 参数会把日志等级提升到 DEBUG 并在控制台实时显示 WebSocket 报文。

---

## 八、构建可执行文件

```powershell
pip install pyinstaller websockets blackboxprotobuf aiohttp websocket pysqlcipher3
pyinstaller --clean build.spec
```

`build.spec` 已配置好静态资源（`index.html`、`html_templates/`、`export_config.json`），`datas` 列表确保模板与默认配置随 exe 一起分发。最终产物 `dist/QQ聊天记录导出工具.exe` 与 3 个 `*.decrypt.db` 放在同一目录即可双击运行。

注意：3 个 `.db` 是动态的，**不要** 打包进 exe。`export_config.json` 也会优先在 exe 所在目录创建/读取，从而实现配置持久化。

---

## 九、技术参考

- [Tealina28/QQNT_Export](https://github.com/Tealina28/QQNT_Export) — 程序框架与 Protobuf 定义。
- [QQBackup/qq-win-db-key](https://github.com/QQBackup/qq-win-db-key) — 数据库解密、Protobuf 定义、数据库表结构。
- [docs.aaqwq.top](https://docs.aaqwq.top/) — QQNT 数据库解密教程与 `pass key` 计算工具。

---

## 十、常见问题

**Q1：启动时弹出“缺少 sqlcipher.exe 或 sqlite3.exe”。**
确保 `sqlcipher.exe`、`sqlite3.exe`、`decrypt.config` 与待解密的 `*.clean.db` 在同一目录。`--sqlcipher` 与启动时的「数据库源选择 2」都会走这条路径。

**Q2：解密过程中报 `Parse error near line 1: near "ok": syntax error`。**
这是 SQLCipher 旧版本对 `PRAGMA cipher is no longer supported` 的告警。程序会记录到日志但 **不中断流程**，最终以解密后文件是否成功生成作为判断标准。

**Q3：Web UI 打开后左侧为空。**
确认 `profile_info.decrypt.db` 存在且能正常打开；可在 CLI 下执行 `list friends` 验证。

**Q4：群成员显示「群聊(123456)」而不是真实群名。**
确保 `group_info.db` 已解密并放在工作目录；缺失时只会显示群号占位符。

**Q5：想要自定义 HTML 模板。**
把模板放入 `html_templates/`，然后在 Web UI「导出配置」或 `export_config.json` 中修改 `html_template` 字段。

**Q6：导出文件存放在哪？**
默认 `<工作目录>/<我的QQ号>_output/`，可使用 `--location` 或 Web UI 中的导出位置参数覆盖。

**Q7：导出文件怎么命名？**

- `c2c_<好友备注或昵称>_<QQ号>_<时间戳>.md` — 私聊记录
- `group_<群名>_<群号>_<时间戳>.md` — 群聊记录
- `c2c_*_timeline.md` / `group_*_timeline.md` — 时间线模式下的合并文件
- 时间线合并模式下，所有会话会整合成单个 `chat_logs_timeline_<时间戳>.md` / `.html`
- `--group-dirs` 启用时，私聊按 `Individual/Friends/<分组名>/` 分子目录


## 十一、免责声明

**本项目仅供学习交流使用，严禁用于任何违反中国大陆法律法规、您所在地区法律法规、QQ 软件许可及服务协议的行为，开发者不承担任何相关行为导致的直接或间接责任。**

**本项目不对生成内容的完整性、准确性作任何担保，生成的一切内容不可用于法律取证，您不应当将其用于学习与交流外的任何用途。**

---

# QQNT Chat History Export Tool (ARK-1) — English

A Windows-oriented tool to preview and export QQNT chat history. The single `server.py` ships in three modes:

- **Web UI (default)** — `aiohttp` + `websockets` panel for browsing, decoding, and exporting.
- **Interactive CLI** — `python server.py --cli` exposes a `do_help / list / export / decrypt / config / webui` prompt.
- **Headless CLI** — one-shot `python server.py --export-...` for batch automation.
- **Direct SQLCipher pipeline** — `--sqlcipher` (or interactive prompt) streams `*.clean.db` through `sqlcipher.exe | sqlite3.exe` into `*.decrypt.db` using the PRAGMA list in `decrypt.config`. No SQLiteStudio, no `tail`.
- **Live Web panel** — three-pane UI with rich message rendering (image, file, voice, video, red packet, recall, poke, reply, gray tip, ARK card).
- **Deeper group integration** — auto loads `group_info.db` for accurate group cards, member export, essences, bulletins, and notifications.
- **Multiple output formats** — `md` / `txt` / `html` (templated) / `json` / `csv` plus `json-custom` / `csv-custom`.
- **Inline API docs** — `/api-docs` plus `GET /api?command=...` for external automation.
- **Single-file build** — `build.spec` packages the whole tool into one `.exe`.

## Quick Start

```powershell
# 1. Decrypt the QQNT databases (see below) so you have:
nt_msg.decrypt.db
profile_info.decrypt.db
group_info.decrypt.db

# 2. Put them next to ark-v9-sqlcipher解密支持.exe (or server.py)

# 3. Launch
python server.py
# Browser opens http://localhost:9060 automatically.
```

If you still have the raw `*.clean.db` files, drop `sqlcipher.exe`, `sqlite3.exe`, and `decrypt.config` in the same folder and run:

```powershell
python server.py --sqlcipher
```

## Workflow

1. **Strip the 1024-byte private header** from `nt_msg.db` first — QQNT prepends 1024 bytes of proprietary data on top of the SQLCipher ciphertext. Any of these methods works:
   - **Hex editor (Windows)**: open `nt_msg.db` in HxD, select and delete the first 1024 bytes, save as `nt_msg.clean.db`.
   - **Linux `tail`**: `tail -c +1025 nt_msg.db > nt_msg.clean.db`.
   - **Python one-liner**: `python -c "open('nt_msg.clean.db','wb').write(open('nt_msg.db','rb').read()[1024:])"`.
   - `profile_info.db` and `group_info.db` do **not** need this step.
2. **Decrypt the databases** — either with this tool's `--sqlcipher` flag, or via the upstream SQLiteStudio + `sqlite3 .read` flow. The first option only requires the PRAGMA list in `decrypt.config`; the second needs the GUI tool plus a `sqlite3` binary on `PATH`.
3. **Place** the three `*.decrypt.db` files into the working directory.
4. **Launch** `server.py` (or the bundled `.exe`) — the Web UI opens on `http://localhost:9060`.
5. **Browse** friends / groups, **preview** decoded messages, and **export** using the right panel.
6. Inspect the per-run log under `log/arklog-*.log` for diagnostics.

## Output File Naming


- `c2c_<remark-or-nick>_<qq>_<timestamp>.md` — private chat
- `group_<group-name>_<group-uin>_<timestamp>.md` — group chat
- `c2c_*_timeline.md` / `group_*_timeline.md` — timeline mode files
- `chat_logs_timeline_<timestamp>.md` / `.html` — merged timeline covering all selected chats
- `--group-dirs` puts private chats under `Individual/Friends/<group-name>/`

## CLI at a Glance

```powershell
python server.py --list-friends
python server.py --mode individual --friends all --format md
python server.py --mode timeline --groups 123456789 --format html
python server.py --export-extra --group 123456789 --type members
python server.py --export-raw --db nt_msg.decrypt.db --table c2c_msg_table --columns 40020,40050,40800 --raw-format json
python server.py --sqlcipher --overwrite
```

See the [CLI 参数速查](#四cli-参数速查) section above for the full reference.

## Web API

`http://localhost:9060/api?command=<name>`

| Command | Purpose |
| --- | --- |
| `list_friends` / `list_groups` / `list_db_schema` / `list_fields` | Discovery |
| `get_db_info` | Connection state |
| `get_chat_history` | Paginated history (supports `from_ts` / `before_ts`) |
| `export` / `export_extra` / `export_raw` | Trigger the same exporters the UI uses |
| `get_config` / `save_config` | Read / write `export_config.json` |

Progress for long-running exports is streamed over the WebSocket channel.

## Build

```powershell
pip install pyinstaller websockets blackboxprotobuf aiohttp websocket pysqlcipher3
pyinstaller --clean build.spec
```

The `.spec` already wires `index.html`, `html_templates/`, and `export_config.json` as datas. Distribute `dist/QQ聊天记录导出工具.exe` together with the three `*.decrypt.db` files — do **not** bundle the databases into the binary.

## Disclaimer

This project is for learning and communication only. Do not use it for activities that violate the laws of Mainland China, your jurisdiction, or the QQ Software License and Service Agreement. The authors bear no liability for misuse. Generated content is provided "as is" with no warranty of completeness or accuracy and must not be used as legal evidence.
