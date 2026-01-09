# MTK Log LLM Inspector - 使用说明

## 快速开始 / Quick Start

欢迎使用 MTK Log LLM Inspector！这是一个独立的可执行文件，**无需安装 Python**。

Welcome to MTK Log LLM Inspector! This is a standalone executable that **doesn't require Python installation**.

### 启动应用 / Starting the Application

**Windows:**
- 双击 `MTK_Log_Inspector.exe` 即可启动
- Double-click `MTK_Log_Inspector.exe` to launch

**Linux/Mac:**
- 在终端运行：`./MTK_Log_Inspector`
- Run in terminal: `./MTK_Log_Inspector`

## 使用步骤 / Usage Steps

### 1. 配置 API 密钥 / Configure API Key

首次使用需要配置阿里云百炼 API 密钥：

First-time users need to configure Alibaba Cloud Bailian API key:

1. 打开"配置 Configuration"标签页
   Open the "Configuration" tab
2. 输入您的 API Key
   Enter your API Key
3. 选择模型（默认：qwen-plus）
   Select model (default: qwen-plus)
4. 点击"保存 Save"按钮
   Click "Save" button

### 2. 选择日志文件 / Select Log File

1. 打开"分析 Analysis"标签页
   Open the "Analysis" tab
2. 点击"选择文件 Browse"按钮选择日志文件
   Click "Browse" to select log file
3. 或直接拖放日志文件到窗口
   Or drag and drop log file to window

### 3. 输入规范文档（可选但推荐）/ Enter Specification (Optional but Recommended)

在规范文档区域输入日志字段的含义说明，帮助 AI 更好地理解您的日志格式。

Enter the meaning of log fields in the specification area to help AI better understand your log format.

例如 / Example:
```
AudioFlinger: 音频混音器相关日志
Track started: 表示音频轨道开始播放
Stream active: 音频流处于活动状态
```

### 4. 开始分析 / Start Analysis

点击"开始分析 Start Analysis"按钮，应用会自动分析日志并显示结果。

Click "Start Analysis" button, the app will automatically analyze the log and display results.

### 5. 查看和保存结果 / View and Save Results

1. 在"结果 Results"标签页查看分析结果
   View analysis results in "Results" tab
2. 点击"保存结果 Save Results"保存为 JSON 和 Markdown 文件
   Click "Save Results" to save as JSON and Markdown files

## 功能特性 / Features

- 🔍 自动过滤音频相关日志 / Automatic audio log filtering
- 🤖 使用大语言模型分析音频状态 / LLM-powered audio state analysis
- 📊 生成详细的分析报告 / Generate detailed analysis reports
- 🔒 支持数据脱敏 / Data masking support
- 🪟 滑动窗口分析 / Sliding window analysis
- 📝 双格式输出（JSON + Markdown）/ Dual format output

## 系统要求 / System Requirements

- Windows 7 及以上 / Windows 7 or later
- Linux (64-bit) / Linux（64位）
- macOS 10.13 及以上 / macOS 10.13 or later
- 无需安装 Python / No Python installation required
- 需要网络连接访问 API / Internet connection required for API access

## 获取 API 密钥 / Getting API Key

您需要阿里云百炼（Qwen）API 密钥来使用此工具。

You need an Alibaba Cloud Bailian (Qwen) API key to use this tool.

1. 访问阿里云官网 / Visit Alibaba Cloud website
2. 注册并开通百炼服务 / Register and enable Bailian service
3. 获取 API Key / Get API Key

## 故障排除 / Troubleshooting

**问题：无法启动应用**
**Issue: Cannot start the application**

- Windows: 检查是否被杀毒软件拦截
- Windows: Check if blocked by antivirus software
- 尝试以管理员身份运行
- Try running as administrator

**问题：分析失败**
**Issue: Analysis fails**

- 确认 API 密钥正确
- Confirm API key is correct
- 检查网络连接
- Check network connection
- 确认日志文件有效
- Confirm log file is valid

## 支持 / Support

如有问题，请访问项目主页：
For issues, please visit the project homepage:

https://github.com/Yang-QZ/mtk-log-llm-inspector

## 许可证 / License

请参见项目仓库中的 LICENSE 文件。
See LICENSE file in the project repository.
