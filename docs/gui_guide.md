# GUI 使用指南 / GUI User Guide

## 概述 / Overview

MTK Log LLM Inspector 现在提供了友好的图形用户界面（GUI），特别针对 Windows 11 用户优化。无需命令行操作，即可完成日志分析。

MTK Log LLM Inspector now provides a user-friendly graphical interface (GUI), especially optimized for Windows 11 users. You can complete log analysis without command line operations.

## 系统要求 / System Requirements

- **操作系统 / OS**: Windows 11, Windows 10, macOS, or Linux
- **Python**: 3.8 或更高版本 / 3.8 or higher
- **依赖项 / Dependencies**: 
  - tkinter (Python 标准库自带 / Included with Python)
  - requests
  - pytest (仅用于开发测试 / For development testing only)

## 安装与启动 / Installation and Launch

### 1. 安装 Python / Install Python

如果尚未安装 Python，请从 [python.org](https://www.python.org/downloads/) 下载并安装。
安装时请确保勾选"Add Python to PATH"选项。

If Python is not installed, download and install it from [python.org](https://www.python.org/downloads/).
Make sure to check the "Add Python to PATH" option during installation.

### 2. 克隆仓库并安装依赖 / Clone Repository and Install Dependencies

```bash
git clone https://github.com/Yang-QZ/mtk-log-llm-inspector.git
cd mtk-log-llm-inspector
pip install -r requirements.txt
```

### 3. 启动 GUI / Launch GUI

**Windows 用户 / Windows Users:**
双击 `run_gui.bat` 文件，或在命令提示符中运行：
Double-click `run_gui.bat`, or run in Command Prompt:

```cmd
run_gui.bat
```

**所有平台 / All Platforms:**
```bash
python run_gui.py
```

## 界面介绍 / Interface Overview

GUI 包含三个主要标签页：
The GUI contains three main tabs:

### 标签页 1: 配置 (Configuration)

![Configuration Tab]

#### LLM API 配置 / LLM API Configuration

1. **API Key**: 输入您的阿里云百炼 API 密钥
   - Enter your Alibaba Cloud Bailian API key
   - 获取方式 / How to get: [阿里云控制台](https://dashscope.console.aliyun.com/)
   - 点击"保存"按钮将 API 密钥保存到本地配置文件
   - Click "Save" to store the API key in local configuration

2. **模型 (Model)**: 选择要使用的大语言模型
   - Select the LLM model to use
   - 选项 / Options:
     - `qwen-plus`: 平衡性能和成本 / Balanced performance and cost (推荐 / Recommended)
     - `qwen-turbo`: 快速响应，成本较低 / Fast response, lower cost
     - `qwen-max`: 最高性能，成本较高 / Highest performance, higher cost

#### 分析参数 / Analysis Parameters

1. **窗口大小 (Chunk Size)**:
   - 每个分析窗口包含的日志行数 / Number of log lines per analysis window
   - 默认值 / Default: 200 行 / lines
   - 建议范围 / Recommended range: 50-500
   - 较大的窗口提供更多上下文，但分析时间更长
   - Larger windows provide more context but take longer to analyze

2. **重叠行数 (Overlap)**:
   - 相邻窗口之间重叠的行数 / Number of overlapping lines between adjacent windows
   - 默认值 / Default: 50 行 / lines
   - 建议范围 / Recommended range: 0-100
   - 重叠有助于避免跨窗口信息丢失
   - Overlap helps avoid losing information across windows

3. **启用数据脱敏 (Enable Data Masking)**:
   - 勾选此选项将自动隐藏敏感信息 / Check to automatically hide sensitive information
   - 包括 / Includes:
     - 邮箱地址 / Email addresses
     - IP 地址 / IP addresses
     - MAC 地址 / MAC addresses
     - 序列号 / Serial numbers

### 标签页 2: 分析 (Analysis)

![Analysis Tab]

#### 日志文件选择 / Log File Selection

1. **文件路径 (File Path)**:
   - 显示当前选择的日志文件路径 / Shows the path of currently selected log file
   - 点击"选择文件"浏览并选择文件 / Click "Browse" to select a file
   - 支持的文件格式 / Supported formats: `.log`, `.txt`

2. **拖拽提示 / Drag and Drop Hint**:
   - 注意：基础版 tkinter 在 Windows 上不直接支持拖拽
   - Note: Basic tkinter doesn't directly support drag-drop on Windows
   - 请使用"选择文件"按钮 / Please use the "Browse" button

#### 规范文档 / Specification Document

这是一个关键功能，用于告诉 LLM 您的日志格式和含义：
This is a key feature to tell the LLM about your log format and meanings:

**应该包含什么 / What to Include:**
- 日志标签的含义 / Meanings of log tags
- 特定字段的解释 / Explanations of specific fields
- 状态代码的定义 / Definitions of status codes
- 任何领域特定的术语 / Any domain-specific terminology

**示例 / Example:**
```
# MTK AudioFlinger 日志规范

## 标签含义
- AudioFlinger: 音频混音服务，负责音频流的混合和输出
- AudioTrack: 代表一个音频播放轨道
- PlaybackThread: 音频播放线程

## 状态说明
- "Track started": 音频轨道开始播放
- "Stream active": 音频流处于活动状态
- "muted": 音频被静音
- "stopped": 音频已停止
```

#### 操作按钮 / Action Buttons

1. **开始分析 (Start Analysis)**:
   - 开始分析所选的日志文件 / Start analyzing the selected log file
   - 分析期间按钮会被禁用 / Button is disabled during analysis
   - 进度会实时显示在进度条中 / Progress is shown in real-time in the progress bar

2. **停止 (Stop)**:
   - 停止正在进行的分析 / Stop the ongoing analysis
   - 注意：当前版本不支持中途停止，此功能为占位
   - Note: Current version doesn't support mid-analysis stop, this is a placeholder

#### 进度显示 / Progress Display

- 状态文本显示当前操作 / Status text shows current operation
- 进度条显示分析进度 / Progress bar shows analysis progress
- 实时更新窗口分析状态 / Real-time updates of window analysis status

### 标签页 3: 结果 (Results)

![Results Tab]

#### 结果显示 / Results Display

显示完整的分析结果，包括：
Shows complete analysis results, including:

1. **窗口分析结果 / Window Analysis Results**:
   - 每个窗口的状态 / State of each window
   - 置信度评分 / Confidence scores
   - 分析进度 / Analysis progress

2. **Markdown 格式报告 / Markdown Format Report**:
   - 分析摘要 / Analysis summary
   - 合并后的片段信息 / Merged segment information
   - 关键证据 / Key evidence
   - 建议的后续操作 / Suggested next actions

#### 操作按钮 / Action Buttons

1. **保存结果 (Save Results)**:
   - 将结果保存到选定的目录 / Save results to selected directory
   - 生成两个文件 / Generates two files:
     - `report.json`: 完整的 JSON 格式报告 / Complete JSON report
     - `report.md`: Markdown 格式摘要 / Markdown summary

2. **清除 (Clear)**:
   - 清空结果显示区域 / Clear the results display area
   - 准备进行下一次分析 / Prepare for next analysis

## 使用流程 / Workflow

### 完整分析流程 / Complete Analysis Workflow

1. **首次使用准备 / First-Time Setup**:
   ```
   配置标签页 → 输入 API Key → 选择模型 → 保存配置
   Configuration Tab → Enter API Key → Select Model → Save Config
   ```

2. **进行分析 / Perform Analysis**:
   ```
   分析标签页 → 选择日志文件 → 输入规范文档 → 开始分析
   Analysis Tab → Select Log File → Enter Spec Doc → Start Analysis
   ```

3. **查看和保存结果 / View and Save Results**:
   ```
   结果标签页 → 查看分析结果 → 保存到文件
   Results Tab → View Results → Save to Files
   ```

## 常见问题 / FAQ

### Q1: 找不到 API Key 怎么办？
### Q1: Where to find API Key?

**A**: 访问阿里云控制台获取：
**A**: Visit Alibaba Cloud console:
1. 登录 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
2. 在"API-KEY 管理"页面创建或查看现有的 API Key
3. 将 API Key 复制并粘贴到 GUI 的配置页面

### Q2: 分析失败怎么办？
### Q2: What if analysis fails?

**A**: 检查以下几点：
**A**: Check the following:
1. API Key 是否正确 / Is the API Key correct?
2. 网络连接是否正常 / Is the network connection normal?
3. 日志文件格式是否正确 / Is the log file format correct?
4. API 配额是否充足 / Is there sufficient API quota?

### Q3: 如何提高分析准确度？
### Q3: How to improve analysis accuracy?

**A**: 
1. **提供详细的规范文档** / Provide detailed specification document
   - 越详细越好 / The more detailed, the better
   - 包含具体的日志示例 / Include specific log examples

2. **调整窗口参数** / Adjust window parameters
   - 增大窗口大小以提供更多上下文 / Increase window size for more context
   - 增加重叠以避免信息丢失 / Increase overlap to avoid information loss

3. **选择合适的模型** / Choose appropriate model
   - qwen-max 提供最高准确度 / qwen-max provides highest accuracy
   - qwen-plus 是性能和成本的平衡选择 / qwen-plus is balanced choice

### Q4: 配置保存在哪里？
### Q4: Where is the configuration saved?

**A**: 配置文件保存在用户主目录：
**A**: Configuration is saved in user home directory:
- Windows: `C:\Users\YourUsername\.mtk_log_inspector_config.json`
- macOS/Linux: `~/.mtk_log_inspector_config.json`

### Q5: 支持哪些日志格式？
### Q5: What log formats are supported?

**A**: 
- 主要支持 Android logcat 格式 / Primarily supports Android logcat format
- 也可以分析任何文本格式的日志 / Can also analyze any text format logs
- 音频标签过滤是可选的 / Audio tag filtering is optional

### Q6: 分析需要多长时间？
### Q6: How long does analysis take?

**A**: 时间取决于：
**A**: Time depends on:
- 日志文件大小 / Log file size
- 窗口数量 / Number of windows
- API 响应速度 / API response speed
- 网络延迟 / Network latency

典型的 1000 行日志大约需要 1-2 分钟。
A typical 1000-line log takes about 1-2 minutes.

## 高级技巧 / Advanced Tips

### 1. 批量处理 / Batch Processing

虽然 GUI 一次只能处理一个文件，但您可以：
Although GUI processes one file at a time, you can:
- 分析完一个文件后立即分析下一个 / Analyze next file immediately after completing one
- 或使用 CLI 进行批量处理 / Or use CLI for batch processing

### 2. 自定义规范模板 / Custom Specification Templates

为常用的日志类型创建规范文档模板：
Create specification document templates for common log types:
```
templates/
  ├── audio_spec.md
  ├── system_spec.md
  └── network_spec.md
```

在分析时复制粘贴相应的模板内容。
Copy and paste the appropriate template content when analyzing.

### 3. 结果对比 / Results Comparison

保存多次分析的结果，使用文本对比工具比较：
Save results from multiple analyses and compare using text diff tools:
- 了解参数变化对结果的影响 / Understand how parameter changes affect results
- 发现日志中的模式和趋势 / Discover patterns and trends in logs

## 故障排除 / Troubleshooting

### 问题：GUI 无法启动
### Issue: GUI won't start

**可能原因 / Possible Causes:**
1. Python 未正确安装 / Python not properly installed
2. tkinter 模块缺失 / tkinter module missing

**解决方案 / Solutions:**
```bash
# 检查 Python 版本
# Check Python version
python --version

# 检查 tkinter
# Check tkinter
python -c "import tkinter; print('OK')"

# 如果缺少 tkinter (Linux)
# If tkinter is missing (Linux)
sudo apt-get install python3-tk
```

### 问题：分析卡住不动
### Issue: Analysis gets stuck

**可能原因 / Possible Causes:**
1. 网络连接问题 / Network connectivity issues
2. API 服务暂时不可用 / API service temporarily unavailable

**解决方案 / Solutions:**
1. 检查网络连接 / Check network connection
2. 等待几分钟后重试 / Wait a few minutes and retry
3. 查看 API 服务状态页 / Check API service status page

### 问题：结果不准确
### Issue: Results are inaccurate

**改进建议 / Improvement Suggestions:**
1. 提供更详细的规范文档 / Provide more detailed specification document
2. 调整窗口大小和重叠参数 / Adjust window size and overlap parameters
3. 尝试更高级的模型 (qwen-max) / Try a more advanced model (qwen-max)
4. 确保日志文件完整且格式正确 / Ensure log file is complete and properly formatted

## 安全性 / Security

1. **API Key 安全 / API Key Security**:
   - API Key 保存在本地配置文件中 / API Key is stored in local configuration file
   - 文件只有当前用户可读 / File is only readable by current user
   - 永远不要分享您的 API Key / Never share your API Key
   - 定期轮换 API Key / Regularly rotate API Key

2. **数据隐私 / Data Privacy**:
   - 启用数据脱敏以保护敏感信息 / Enable data masking to protect sensitive information
   - 分析过程中数据通过 HTTPS 传输 / Data is transmitted via HTTPS during analysis
   - 不会存储您的日志到云端 / Your logs are not stored in the cloud

3. **配置文件安全 / Configuration File Security**:
   - 配置文件存储在用户主目录 / Config file is stored in user home directory
   - 使用文件系统权限保护 / Protected by file system permissions
   - 可以手动删除以清除配置 / Can be manually deleted to clear configuration

## 反馈与支持 / Feedback and Support

如有问题或建议，请：
For questions or suggestions, please:

1. 查看项目 README / Check project README
2. 提交 GitHub Issue / Submit a GitHub Issue
3. 参与讨论区 / Join the discussion forum

## 更新日志 / Changelog

### v0.1.0 (2024-01-08)
- ✨ 新增 GUI 界面 / Added GUI interface
- 🔧 配置管理功能 / Configuration management
- 📝 规范文档输入 / Specification document input
- 💾 结果保存功能 / Results saving functionality
- 🎨 友好的用户界面 / User-friendly interface
