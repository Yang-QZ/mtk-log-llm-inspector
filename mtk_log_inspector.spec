# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MTK Log LLM Inspector GUI
MTK日志大语言模型分析器GUI的PyInstaller配置文件

This spec file is used to build a standalone executable for Windows, Linux, and macOS.
此配置文件用于构建Windows、Linux和macOS的独立可执行文件。
"""

from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

# Collect all data files from docs directory
docs_datas = [
    ('docs/prompt.md', 'docs'),
]

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=docs_datas,
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'requests',
    ],
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
    name='MTK_Log_Inspector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add an icon file later if available
)
