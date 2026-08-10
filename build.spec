# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['server.py'],  # 你的主程序文件名
    pathex=[],
    binaries=[],
    datas=[
        ('index.html', '.'),
        ('ark-invest.html', '.'),
        ('api_docs.html','.'),
        ('html_templates', 'html_templates'),
        ('export_config.json', '.'),
        ('lib', 'lib'),
        ('icon.ico', '.')
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
    icon='icon.ico',            # 你可以指定一个.ico文件作为图标
)
