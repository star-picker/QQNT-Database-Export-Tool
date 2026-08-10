应用程序打包流程 (使用 PyInstaller)
本文档将指导您如何将 Python 应用程序打包成一个独立的 Windows 可执行文件 (.exe)。

1. 环境准备
在开始之前，请确保您的 Python 环境中安装了所有必要的库。

首先，安装 PyInstaller，这是我们的打包工具：

pip install pyinstaller

然后，确保您的程序所依赖的所有库都已安装。根据您的 server.py 代码，至少需要以下库：

pip install websockets blackboxprotobuf
pip install websocket
pip install aiohttp
pip install pysqlcipher3

2. 修改源代码 (已完成)
我已经为您提供了一个修改版的 server_modified.py。主要的修改包括：

动态路径适配：使用一个 get_resource_path 函数来判断程序是在开发环境（.py）还是打包环境（.exe）中运行，从而正确地定位 index.html, html_templates 和 export_config.json 等资源文件。

自动打开浏览器：在服务器启动后，程序会自动调用默认浏览器打开 index.html 控制面板。

打包后的工作目录：打包后的 .exe 会将自身所在的目录作为工作目录，用户只需将3个数据库文件 (nt_msg.decrypt.db, profile_info.decrypt.db, group_info.decrypt.db) 和 exe 文件放在同一个文件夹下即可。

更友好的提示：为打包后的用户提供了更清晰的指引。

请使用 server_modified.py 文件进行后续操作。

3. 创建 PyInstaller 配置文件 (.spec)
PyInstaller 使用一个 .spec 文件来精确控制打包过程。这是最关键的一步，它告诉打包工具需要包含哪些额外的文件和目录。

在您的项目根目录下（与 server_modified.py 同级），创建一个名为 build.spec 的文件，并将以下内容复制进去：

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['server.py'],  # 你的主程序文件名
    pathex=[],
    binaries=[],
    datas=[
        ('index.html', '.'),
        ('html_templates', 'html_templates'),
        ('export_config.json', '.')
    ],
    hiddenimports=['websockets.legacy', 'websockets.legacy.client', 'websockets.legacy.server','blackboxprotobuf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QQ聊天记录导出工具',  # 生成的exe文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,         # 设置为True，保留命令行窗口，方便查看日志和错误
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,            # 你可以指定一个.ico文件作为图标
)




.spec 文件解析：
Analysis(['server_modified.py'], ...): 指定了主入口文件是 server_modified.py。

datas=[ ... ]: 这是核心部分，用于添加非代码资源。

('index.html', '.'): 将项目根目录下的 index.html 文件添加到打包后的根目录。

('html_templates', 'html_templates'): 将 html_templates 整个文件夹及其内容添加到打包后的 html_templates 文件夹中。

('export_config.json', '.'): 将 export_config.json 添加到打包后的根目录。

hiddenimports=[...]: 有些库的子模块 PyInstaller 可能检测不到，需要在这里手动添加。websockets 就有这种情况。

name='QQ聊天记录导出工具': 设置生成的 .exe 文件的名字。

console=True: 这会保留一个命令行窗口。对于您这种后台服务程序来说，这是必须的，否则程序会一闪而过。用户可以通过这个窗口看到程序的运行日志，并在使用完毕后关闭它来结束程序。

4. 执行打包命令
现在，万事俱备。打开命令行工具（如 CMD 或 PowerShell），cd 到您的项目根目录，然后运行以下命令：

pyinstaller --clean build.spec

--clean: 这个参数会在打包前清理之前生成的文件，避免旧文件造成干扰。

打包过程可能需要几分钟。完成后，您会在项目根目录下看到两个新的文件夹：build 和 dist。

5. 验证和分发
您最终需要的可执行文件位于 dist 文件夹内。

最终交付给用户的文件结构应该是这样的：

/最终分发文件夹/
├── QQ聊天记录导出工具.exe         <-- 这是从 dist 文件夹中拷贝出来的程序
├── nt_msg.decrypt.db           <-- 用户提供的数据库文件
├── profile_info.decrypt.db     <-- 用户提供的数据库文件
└── group_info.decrypt.db       <-- 用户提供的数据库文件 (可选)

使用流程：
用户将这几个文件放在同一个文件夹里。

双击运行 QQ聊天记录导出工具.exe。

一个命令行窗口会弹出，显示服务器启动日志。

程序会自动在用户的默认浏览器中打开控制面板 (index.html)。

用户在网页上进行所有操作。

使用完毕后，直接关闭弹出的那个命令行窗口即可。

重要提示：

您的三个数据库文件 (.db) 是动态变化的，绝对不能打包进 .exe 文件。现在的流程保证了这一点，程序总是在运行时从 .exe 所在的目录读取数据库。

静态资源 (index.html, html_templates 等) 已经被打包进去了，所以您分发时只需要 .exe 文件。

export_config.json 虽然也被打包进去作为默认配置，但修改后的代码会优先在 .exe 所在目录生成和读取新的配置文件，实现了配置的持久化。