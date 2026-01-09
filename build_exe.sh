#!/bin/bash
# Build script for MTK Log LLM Inspector GUI executable
# MTK日志分析工具GUI可执行文件构建脚本

echo "========================================"
echo "MTK Log LLM Inspector - Build Executable"
echo "MTK日志分析工具 - 构建可执行文件"
echo "========================================"
echo

# Check if PyInstaller is installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    echo "未找到PyInstaller，正在安装..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo
        echo "Error: Failed to install PyInstaller"
        echo "错误：安装PyInstaller失败"
        exit 1
    fi
fi

echo
echo "Building executable..."
echo "正在构建可执行文件..."
echo

# Build using PyInstaller with the spec file
pyinstaller --clean --noconfirm mtk_log_inspector.spec

if [ $? -ne 0 ]; then
    echo
    echo "Error: Build failed"
    echo "错误：构建失败"
    exit 1
fi

echo
echo "========================================"
echo "Build completed successfully!"
echo "构建成功完成！"
echo "========================================"
echo
echo "The executable is located at:"
echo "可执行文件位于："
echo "  dist/MTK_Log_Inspector"
echo
echo "You can distribute this file to users who don't have Python installed."
echo "您可以将此文件分发给未安装Python的用户。"
echo
