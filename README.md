# QQNT-Database-Export-Tool
一个基于 Python 的工具，用于将已解密的 QQNT 数据库中的聊天记录导出。
A Python based tool for exporting chat history from a decrypted QQNT database.

-----

### 中文版

### QQNT 聊天记录导出工具使用说明

#### 前置条件：解密 QQNT 数据库

在使用本工具前，您需要先解密您的 QQNT 数据库。以下以解密 **QQNT\_Android** 数据库为例，其他版本请参考相关文档。

1.  **参考文档**：

      * 请参阅 [https://docs.aaqwq.top/](https://docs.aaqwq.top/) 的解密教程，以获取 `nt_uid` 和 `rand`，并使用其内置工具计算出 `QQ_path_hash` 和 `pass key`。

2.  **处理 `nt_msg.db` 文件**：

      * 删除 `nt_msg.db` 文件的前 1024 个字节。您可以使用以下任一方法：
          * **二进制编辑器**：使用如 Windows 上的 HxD 或其他类似软件进行操作。
          * **Linux `tail` 命令**：`tail -c +1025 nt_msg.db > nt_msg.clean.db`
          * **Python 脚本**：`python -c "open('nt_msg.clean.db','wb').write(open('nt_msg.db','rb').read()[1024:])"`
      * 完成后，您将得到一个名为 `nt_msg.clean.db` 的文件。

3.  **使用 SQLiteStudio 导出数据库**：

      * 使用 SQLiteStudio 打开 `nt_msg.clean.db`，并输入以下数据库参数进行配置：

    <!-- end list -->

    ```sql
    PRAGMA key = 'pass key'; # 'pass key' 是您之前计算出的数据库密钥
    PRAGMA cipher_page_size = 4096;
    PRAGMA kdf_iter = 4000;
    PRAGMA cipher_hmac_algorithm = HMAC_SHA1; # 请参考 https://docs.aaqwq.top/ 按照实际情况填写
    PRAGMA cipher_default_kdf_algorithm = PBKDF2_HMAC_SHA512;
    PRAGMA cipher = 'aes-256-cbc';
    ```

      * 导出数据库内容为一个 SQL 命令文件（例如 `nt_msg.sql`）。

4.  **使用 `sqlite3` 命令行工具**：

      * 从 [SQLite3 官网](https://www.sqlite.org/download.html) 下载全套可执行程序，并将其路径添加到系统环境变量（PATH）中。
      * 进入 SQL 文件所在的目录，在命令行（CMD/Terminal）中执行以下命令以生成解密的数据库文件：

    <!-- end list -->

    ```bash
    sqlite3 nt_msg.decrypt.db ".read nt_msg.sql"
    ```

      * **注意：** 此方法为一种简单粗暴的导出方式，如果您有更好的方法，欢迎提交 Issue。

### 本项目使用指南

#### 1\. 准备工作

  * 安装最新版 **Python**。
  * 安装 `uv` 包管理器：
    ```bash
    pip install uv --index-url=https://pypi.org/simple/ --trusted-host pypi.org
    ```
  * 使用 `uv` 安装所有依赖：
    ```bash
    uv sync
    ```

#### 2\. 使用步骤

1.  **激活虚拟环境**：
      * 在命令行中执行以下命令以激活虚拟环境：
    <!-- end list -->
    ```bash
    .venv\Scripts\activate.bat
    ```
2.  **准备主程序文件**：
      * 将您需要使用的 `main-xxxx.py` 文件重命名为 `main.py`。
3.  **放置数据库文件**：
      * 将解密后的数据库文件 `nt_msg.decrypt.db` 放在项目的根目录。
4.  **执行程序**：
      * 在已激活的虚拟环境中，执行以下命令：
    <!-- end list -->
    ```bash
    python main.py --format json/csv/txt
    ```
      * **`--format`** 参数用于指定导出格式，默认为 `json`。
      * **示例：** 如果您想导出所有纯文本聊天记录为 `.txt` 文件，请输入：
        `python main.py --format txt`
5.  **结果**：
      * 如果一切正常，导出的聊天记录文件将存储在 `chathistory` 文件夹中。
      * 以 `c2c` 开头的文件为私聊记录，以 `group` 开头的文件为群聊记录。

### 技术参考

本项目的灵感和技术参考主要来自以下优秀开源项目：

  * **[Tealina28/QQNT\_Export](https://github.com/Tealina28/QQNT_Export?tab=readme-ov-file)**：程序框架与 `protobuf` 定义。
  * **[QQBackup/qq-win-db-key](https://github.com/QQBackup/qq-win-db-key)**：数据库解密、`protobuf` 定义、数据库表定义。
  * **[https://docs.aaqwq.top/](https://docs.aaqwq.top/)**：数据库解密、`protobuf` 定义、数据库表定义。

-----

### English Version

### QQNT Chat History Export Tool - User Guide

#### Prerequisites: Decrypting the QQNT Database

Before using this tool, you need to decrypt your QQNT database. The following steps use the **QQNT\_Android** database as an example. For other versions, please refer to the corresponding documentation.

1.  **Reference Documentation**:

      * Refer to the decryption tutorial at [https://docs.aaqwq.top/](https://docs.aaqwq.top/) to obtain `nt_uid` and `rand`. Use the built-in tools on the site to calculate `QQ_path_hash` and `pass key`.

2.  **Processing the `nt_msg.db` file**:

      * Remove the first 1024 bytes from the `nt_msg.db` file using one of the following methods:
          * **Binary Editor**: Use a software like HxD on Windows.
          * **Linux `tail` command**: `tail -c +1025 nt_msg.db > nt_msg.clean.db`
          * **Python Script**: `python -c "open('nt_msg.clean.db','wb').write(open('nt_msg.db','rb').read()[1024:])"`
      * After this step, you will have a new file named `nt_msg.clean.db`.

3.  **Using SQLiteStudio to Export the Database**:

      * Open `nt_msg.clean.db` with SQLiteStudio and configure the following database parameters:

    <!-- end list -->

    ```sql
    PRAGMA key = 'pass key'; -- 'pass key' is the database key you calculated earlier
    PRAGMA cipher_page_size = 4096;
    PRAGMA kdf_iter = 4000;
    PRAGMA cipher_hmac_algorithm = HMAC_SHA1; -- Refer to https://docs.aaqwq.top/ and adjust as needed
    PRAGMA cipher_default_kdf_algorithm = PBKDF2_HMAC_SHA512;
    PRAGMA cipher = 'aes-256-cbc';
    ```

      * Export the database content to an SQL command file (e.g., `nt_msg.sql`).

4.  **Using the `sqlite3` Command-line Tool**:

      * Download the full set of `sqlite3` executables from the [official SQLite3 website](https://www.sqlite.org/download.html) and add their path to your system's PATH environment variable.
      * Navigate to the directory containing the SQL file. In your command line (CMD/Terminal), execute the following command to generate a decrypted database file:

    <!-- end list -->

    ```bash
    sqlite3 nt_msg.decrypt.db ".read nt_msg.sql"
    ```

      * **Note:** This is a straightforward method for exporting. If you have a better approach, feel free to submit an issue.

### How to Use This Project

#### 1\. Setup

  * Install the latest version of **Python**.
  * Install the `uv` package manager:
    ```bash
    pip install uv --index-url=https://pypi.org/simple/ --trusted-host pypi.org
    ```
  * Install all dependencies using `uv`:
    ```bash
    uv sync
    ```

#### 2\. Usage Steps

1.  **Activate the Virtual Environment**:
      * In your command line, run the following command to activate the virtual environment:
    <!-- end list -->
    ```bash
    .venv\Scripts\activate.bat
    ```
2.  **Prepare the Main Script**:
      * Rename the desired `main-xxxx.py` file to `main.py`.
3.  **Place the Database File**:
      * Place the decrypted database file, `nt_msg.decrypt.db`, in the root directory of the project.
4.  **Run the Script**:
      * In the activated virtual environment, execute the following command:
    <!-- end list -->
    ```bash
    python main.py --format json/csv/txt
    ```
      * The **`--format`** parameter specifies the export format, with `json` being the default.
      * **Example**: To export all plain text chat logs to `.txt` files, enter:
        `python main.py --format txt`
5.  **Results**:
      * If no errors occur, the exported chat log files will be saved in the `chathistory` folder.
      * Files starting with `c2c` are private chat logs, and files starting with `group` are group chat logs.

### Technical References

This project is inspired by and references the following excellent open-source projects:

  * **[Tealina28/QQNT\_Export](https://github.com/Tealina28/QQNT_Export?tab=readme-ov-file)**: For the program framework and `protobuf` definitions.
  * **[QQBackup/qq-win-db-key](https://github.com/QQBackup/qq-win-db-key)**: For database decryption, `protobuf` definitions, and database table definitions.
  * **[https://docs.aaqwq.top/](https://docs.aaqwq.top/)**: For database decryption, `protobuf` definitions, and database table definitions.
