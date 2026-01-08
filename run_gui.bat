@echo off
REM MTK Log LLM Inspector GUI Launcher for Windows
REM Windows启动脚本

echo Starting MTK Log LLM Inspector GUI...
echo 正在启动 MTK 日志分析工具...

python run_gui.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start the application
    echo 错误：启动应用程序失败
    echo.
    echo Please make sure Python is installed and in your PATH
    echo 请确保已安装Python并已添加到系统PATH
    pause
)
