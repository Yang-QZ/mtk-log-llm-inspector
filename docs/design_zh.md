# MTK Log LLM Inspector 设计文档

## 项目简介

MTK Log LLM Inspector 是一个用于分析 Android 音频日志的智能工具，它利用阿里云百炼（通义千问）大语言模型来自动识别音频播放状态。该工具能够处理大量的 logcat 日志文件，通过滑动窗口的方式分块分析，最终生成详细的分析报告。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户输入                                 │
│              (Android Logcat 日志文件 + 命令行参数)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CLI 命令行接口                              │
│                        (cli.py)                                  │
│  - 参数解析                                                       │
│  - 流程协调                                                       │
│  - 组件初始化                                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌─────────────────┐                    ┌─────────────────┐
│  LogParser      │                    │  DataMasker     │
│  (日志解析器)    │                    │  (数据脱敏器)    │
│                 │                    │                 │
│ - 读取日志文件   │                    │ - 隐藏邮箱      │
│ - 过滤音频相关行 │                    │ - 隐藏IP地址    │
│ - 返回过滤列表   │                    │ - 隐藏序列号    │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
                ┌─────────────────┐
                │   LogChunker    │
                │   (日志分块器)   │
                │                 │
                │ - 滑动窗口分割   │
                │ - 窗口重叠设置   │
                │ - 生成窗口列表   │
                └────────┬────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ BailianClient   │            │  SystemPrompt   │
│ (百炼API客户端)  │            │  (系统提示词)    │
│                 │            │                 │
│ - 发送API请求    │            │ - 指导LLM分析   │
│ - 解析JSON响应   │            │ - 定义输出格式   │
│ - 验证结果      │            │ - 规范状态定义   │
└────────┬────────┘            └────────┬────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   每个窗口的分析结果  │
              │                     │
              │ - final_state       │
              │ - confidence        │
              │ - reason            │
              │ - evidence          │
              │ - next_actions      │
              └─────────┬───────────┘
                        │
                        ▼
                ┌─────────────────┐
                │ WindowAnalyzer  │
                │ (窗口分析器)     │
                │                 │
                │ - 合并相同状态   │
                │ - 生成片段      │
                │ - 创建报告      │
                └────────┬────────┘
                         │
                         ▼
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌─────────────────┐            ┌─────────────────┐
│  report.json    │            │   report.md     │
│  (JSON报告)      │            │  (Markdown报告) │
│                 │            │                 │
│ - 完整元数据     │            │ - 人类可读摘要   │
│ - 所有窗口结果   │            │ - 片段汇总      │
│ - 合并片段      │            │ - 关键证据      │
└─────────────────┘            └─────────────────┘
```

## 核心模块说明

### 1. cli.py - 命令行接口模块

**作用**: 程序的主入口，负责整个分析流程的协调和控制。

**主要功能**:
- **参数解析**: 使用 argparse 解析命令行参数（日志文件路径、输出目录、窗口大小、重叠大小等）
- **组件初始化**: 创建并配置所有必需的组件实例
- **流程编排**: 按顺序调用各个模块，协调整个分析流程
- **结果输出**: 生成 JSON 和 Markdown 格式的分析报告
- **错误处理**: 捕获和处理各种异常情况

**关键函数**:
- `main()`: CLI 主入口，设置参数解析器
- `analyze_command()`: 执行具体的分析流程
- `load_system_prompt()`: 从文件加载系统提示词
- `save_debug_files()`: 保存调试信息（可选）

**工作流程**:
1. 验证输入文件是否存在
2. 创建输出目录
3. 初始化各个组件（解析器、分块器、API客户端等）
4. 加载系统提示词
5. 解析和过滤日志文件
6. 可选地应用数据脱敏
7. 将日志分割成窗口
8. 逐个分析窗口，调用大语言模型
9. 合并相同状态的连续窗口
10. 生成并保存分析报告

### 2. log_parser.py - 日志解析模块

**作用**: 负责读取和过滤日志文件，提取音频相关的日志行。

**主要功能**:
- **文件读取**: 读取 logcat 格式的日志文件，处理编码问题
- **音频过滤**: 使用预定义的音频标签列表过滤相关日志行
- **正则匹配**: 使用正则表达式进行高效的标签匹配

**核心类**:
- `LogParser`: 日志解析器类

**关键方法**:
- `parse_file()`: 读取日志文件，返回所有行
- `filter_audio_lines()`: 过滤出包含音频相关标签的行
- `parse_and_filter()`: 组合上述两个操作，直接返回过滤后的结果

**默认音频标签**:
```python
DEFAULT_AUDIO_TAGS = [
    "AudioFlinger", "AudioTrack", "AudioPolicyService",
    "AudioSystem", "AudioManager", "MediaPlayer",
    "AudioService", "audio_hw", "AudioEffect",
    "AudioMixer", "AudioRecord", "PlaybackThread",
    "RecordThread", "audio"
]
```

**特点**:
- 不区分大小写的匹配
- 使用单词边界，确保精确匹配
- 可自定义音频标签列表
- 忽略读取错误，提高容错性

### 3. masker.py - 数据脱敏模块

**作用**: 移除日志中的敏感信息，保护用户隐私和数据安全。

**主要功能**:
- **邮箱脱敏**: 将邮箱地址替换为 `[EMAIL]`
- **IP地址脱敏**: 将 IPv4 和 IPv6 地址替换为 `[IPv4]` 和 `[IPv6]`
- **MAC地址脱敏**: 将 MAC 地址替换为 `[MAC]`
- **序列号脱敏**: 将设备序列号替换为 `[SERIAL]`

**核心类**:
- `DataMasker`: 数据脱敏器类

**关键方法**:
- `mask_line()`: 对单行日志进行脱敏
- `mask_lines()`: 批量处理多行日志

**正则表达式模式**:
- 邮箱: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}`
- IPv4: `(?:\d{1,3}\.){3}\d{1,3}`
- IPv6: `(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}`
- MAC: `(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}`

**特点**:
- 可选功能，通过 `--mask` 参数启用
- 在发送到 LLM 之前处理，确保隐私
- 采用保守策略，避免误判

### 4. chunker.py - 日志分块模块

**作用**: 将长日志分割成可管理的重叠窗口，便于逐段分析。

**主要功能**:
- **滑动窗口**: 按照指定大小创建日志窗口
- **窗口重叠**: 在相邻窗口间设置重叠区域，避免遗漏信息
- **索引管理**: 为每个窗口分配唯一索引

**核心类**:
- `LogChunker`: 日志分块器类

**关键方法**:
- `chunk_lines()`: 将日志行列表分割成窗口列表

**关键参数**:
- `chunk_size`: 每个窗口的行数（默认: 200）
- `overlap`: 窗口间重叠的行数（默认: 50）

**窗口划分示例**:
```
假设有 500 行日志，chunk_size=200, overlap=50
窗口 0: 行 0-199   (200 行)
窗口 1: 行 150-349 (200 行, 与窗口0重叠50行)
窗口 2: 行 300-499 (200 行, 与窗口1重叠50行)
```

**特点**:
- 确保每个窗口大小一致（最后一个窗口可能较小）
- 返回 `(窗口索引, 窗口内容)` 的元组列表
- 参数验证，防止无效配置

### 5. bailian_client.py - 百炼API客户端模块

**作用**: 与阿里云百炼大语言模型 API 进行通信，发送日志分析请求。

**主要功能**:
- **API通信**: 通过 HTTP POST 请求与百炼 API 交互
- **请求构建**: 构造符合 API 规范的请求体
- **响应解析**: 解析 API 返回的 JSON 响应
- **结果验证**: 验证返回结果的格式和内容
- **错误处理**: 处理网络错误、超时、格式错误等异常

**核心类**:
- `BailianClient`: 百炼API客户端类

**关键方法**:
- `analyze_log_window()`: 分析单个日志窗口，返回结构化结果
- `get_raw_response()`: 获取原始 API 响应（用于调试）

**配置参数**:
- `api_key`: API 密钥（从 `BAILIAN_API_KEY` 环境变量读取）
- `base_url`: API 基础URL（默认: `https://dashscope.aliyuncs.com/compatible-mode/v1`）
- `model`: 模型名称（默认: `qwen-plus`）
- `timeout`: 请求超时时间（默认: 60秒）

**请求格式**:
```json
{
  "model": "qwen-plus",
  "messages": [
    {"role": "system", "content": "系统提示词..."},
    {"role": "user", "content": "Analyze this log window:\n\n日志内容..."}
  ],
  "temperature": 0.1,
  "response_format": {"type": "json_object"}
}
```

**响应验证**:
- 检查必需字段: `final_state`, `confidence`, `reason`, `evidence`, `next_actions`
- 验证 `final_state` 必须是 `PLAYING`, `MUTED`, 或 `UNKNOWN`
- 验证 `confidence` 在 0.0-1.0 范围内

**特点**:
- 支持环境变量配置
- 自动验证响应格式
- 详细的错误信息
- 低温度设置（0.1）确保结果稳定性

### 6. analyzer.py - 分析器模块

**作用**: 处理大语言模型的分析结果，合并相同状态的连续窗口，生成最终报告。

**主要功能**:
- **片段合并**: 将具有相同状态的连续窗口合并为片段
- **证据聚合**: 收集和去重每个片段的关键证据
- **置信度计算**: 计算片段的平均置信度
- **报告生成**: 生成 JSON 和 Markdown 格式的报告

**核心类**:
- `AudioSegment`: 表示一个音频状态片段
- `WindowAnalyzer`: 窗口分析器和报告生成器

**AudioSegment 属性**:
- `state`: 音频状态（PLAYING/MUTED/UNKNOWN）
- `start_window`: 起始窗口索引
- `end_window`: 结束窗口索引
- `confidence_avg`: 平均置信度
- `evidence`: 关键证据列表（最多5条）
- `reasons`: 判断原因列表

**WindowAnalyzer 关键方法**:
- `merge_windows()`: 合并连续的相同状态窗口
- `generate_report()`: 生成完整的 JSON 报告
- `generate_markdown_report()`: 生成人类可读的 Markdown 报告

**合并逻辑**:
```python
如果当前窗口状态 == 上一个窗口状态:
    扩展当前片段
    累加置信度
    添加证据
否则:
    保存当前片段
    开始新片段
```

**报告结构**:

JSON 报告包含:
- `metadata`: 分析元数据（文件路径、时间戳、参数等）
- `summary`: 统计摘要（窗口数、片段数、状态分布）
- `window_results`: 每个窗口的详细分析结果
- `merged_segments`: 合并后的片段列表

Markdown 报告包含:
- 分析时间和文件信息
- 窗口和片段统计
- 每个片段的详细信息和关键证据

**特点**:
- 智能合并，减少冗余
- 证据去重，保持顺序
- 多格式输出，满足不同需求
- 置信度聚合，提供可靠性指标

### 7. __init__.py - 包初始化模块

**作用**: 定义包的版本信息和基本元数据。

**内容**:
```python
__version__ = "0.1.0"
```

**特点**:
- 提供版本号，便于版本管理
- 作为 Python 包的标识文件

## 数据流详解

### 完整数据流程

```
1. 输入阶段
   原始日志文件 (demo.log)
   ↓

2. 解析阶段 (LogParser)
   读取文件 → 过滤音频相关行
   例: 10000 行 → 847 行音频相关
   ↓

3. 脱敏阶段 (DataMasker, 可选)
   隐藏邮箱、IP、序列号等敏感信息
   例: user@example.com → [EMAIL]
   ↓

4. 分块阶段 (LogChunker)
   滑动窗口分割
   例: 847 行 → 5 个窗口
   窗口0: 行0-199
   窗口1: 行150-349 (重叠50行)
   窗口2: 行300-499
   ...
   ↓

5. 分析阶段 (BailianClient)
   对每个窗口:
   - 构造 API 请求
   - 发送到百炼大模型
   - 接收 JSON 响应
   - 验证结果格式
   
   输出示例:
   {
     "window_idx": 0,
     "final_state": "PLAYING",
     "confidence": 0.85,
     "reason": "检测到音频流活动...",
     "evidence": ["AudioFlinger: track started", ...],
     "next_actions": ["Continue monitoring"]
   }
   ↓

6. 合并阶段 (WindowAnalyzer)
   合并相同状态的连续窗口
   例: 5 个窗口 → 3 个片段
   片段1: PLAYING (窗口0-2)
   片段2: MUTED (窗口3)
   片段3: PLAYING (窗口4)
   ↓

7. 输出阶段
   生成两种格式报告:
   - report.json (完整数据)
   - report.md (人类可读摘要)
```

### 关键数据结构

#### 1. 日志行 (List[str])
```python
[
  "01-06 10:15:23.456  1234  1235 I AudioFlinger: Track started",
  "01-06 10:15:24.789  1234  1235 D AudioTrack: Stream active",
  ...
]
```

#### 2. 窗口列表 (List[Tuple[int, List[str]]])
```python
[
  (0, ["line1", "line2", ..., "line200"]),
  (1, ["line151", "line152", ..., "line350"]),
  ...
]
```

#### 3. 窗口分析结果 (Dict)
```python
{
  "window_idx": 0,
  "final_state": "PLAYING",
  "confidence": 0.85,
  "reason": "音频流处于活动状态，检测到播放轨道...",
  "evidence": [
    "AudioFlinger: Track started",
    "AudioTrack: Stream active",
    ...
  ],
  "next_actions": ["Continue monitoring"]
}
```

#### 4. 音频片段 (AudioSegment)
```python
{
  "state": "PLAYING",
  "start_window": 0,
  "end_window": 2,
  "window_count": 3,
  "confidence_avg": 0.88,
  "evidence": [...],  # 最多5条
  "reasons": [...]     # 所有窗口的原因
}
```

## 音频状态定义

系统识别三种音频状态:

### PLAYING (播放中)
**特征**:
- 音频轨道处于活动状态
- 音频流未静音
- 检测到音频路由建立
- 音频硬件处于工作状态

**典型日志模式**:
- "Track started"
- "Stream active"
- "unmuted"
- "routing established"

### MUTED (静音)
**特征**:
- 音频被静音
- 音频流不活动或已停止
- 音频轨道暂停

**典型日志模式**:
- "muted"
- "stream inactive"
- "track stopped"
- "paused"

### UNKNOWN (未知)
**特征**:
- 信息不足以判断
- 存在冲突的信号
- 日志内容模糊

**使用场景**:
- 窗口内容过少
- 日志信息矛盾
- 分析失败或超时

## 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `BAILIAN_API_KEY` | 是 | 无 | 百炼 API 密钥 |
| `BAILIAN_BASE_URL` | 否 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API 基础URL |
| `BAILIAN_MODEL` | 否 | `qwen-plus` | 大模型名称 |

### 命令行参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--log` | 是 | 无 | 输入日志文件路径 |
| `--out` | 是 | 无 | 输出目录路径 |
| `--chunk-size` | 否 | 200 | 每个窗口的行数 |
| `--overlap` | 否 | 50 | 窗口间重叠行数 |
| `--model` | 否 | 从环境变量 | 大模型名称 |
| `--debug` | 否 | False | 启用调试模式 |
| `--mask` | 否 | False | 启用数据脱敏 |

## 运行示例

### 基本使用
```bash
python -m src.cli analyze --log samples/demo.log --out output/
```

### 完整参数
```bash
python -m src.cli analyze \
  --log samples/demo.log \
  --out output/ \
  --chunk-size 200 \
  --overlap 50 \
  --model qwen-plus \
  --debug \
  --mask
```

### 输出文件

**output/report.json** - 完整的 JSON 报告
```json
{
  "metadata": {...},
  "summary": {...},
  "window_results": [...],
  "merged_segments": [...]
}
```

**output/report.md** - Markdown 格式摘要
```markdown
# Audio State Analysis Report
...
```

**output/debug/** (调试模式下)
- `window_0_request.json` - 窗口0的请求数据
- `window_0_response.json` - 窗口0的响应数据
- ...

## 性能考虑

### 时间复杂度
- 日志解析: O(n) - n 为日志行数
- 音频过滤: O(n * m) - m 为标签数量
- 窗口分块: O(n / chunk_size)
- LLM 分析: O(窗口数) - 每个窗口独立处理
- 片段合并: O(窗口数)

### 空间复杂度
- 内存占用主要取决于:
  - 日志文件大小
  - 窗口数量
  - 分析结果缓存

### 优化建议
1. **调整窗口大小**: 较大的窗口减少 API 调用次数，但可能影响分析精度
2. **调整重叠大小**: 较小的重叠减少处理数据量，但可能遗漏跨窗口的信息
3. **使用数据脱敏**: 减少发送到 API 的数据量
4. **批量处理**: 如果处理多个日志文件，可以并行化

## 错误处理

### 常见错误及处理

1. **API 密钥未设置**
   - 错误: `BAILIAN_API_KEY must be set`
   - 解决: 设置环境变量 `export BAILIAN_API_KEY="your-key"`

2. **日志文件不存在**
   - 错误: `Log file not found`
   - 解决: 检查文件路径是否正确

3. **API 请求失败**
   - 错误: `RequestException`
   - 解决: 检查网络连接、API 密钥、配额限制

4. **响应格式错误**
   - 错误: `Invalid response format`
   - 解决: 检查系统提示词是否正确，模型是否支持 JSON 输出

5. **窗口参数无效**
   - 错误: `overlap must be less than chunk_size`
   - 解决: 调整参数确保 overlap < chunk_size

## 扩展性设计

### 可扩展点

1. **新的日志源**: 可以添加不同格式的日志解析器
2. **自定义过滤规则**: 可以配置不同的标签列表或过滤策略
3. **不同的 LLM**: 可以适配其他大语言模型 API
4. **新的输出格式**: 可以添加 HTML、PDF 等输出格式
5. **自定义状态**: 可以定义更多的音频状态类型

### 模块化优势

- 每个模块职责单一，便于维护
- 模块间通过明确的接口通信
- 易于单独测试每个模块
- 可以灵活替换或升级单个模块

## 安全性

### 数据保护
- **API 密钥管理**: 通过环境变量传递，不硬编码
- **调试输出**: 自动隐藏授权头中的密钥
- **数据脱敏**: 可选的敏感信息过滤

### 最佳实践
- 永远不要提交 API 密钥到代码仓库
- 在生产环境中启用 `--mask` 参数
- 定期轮换 API 密钥
- 检查输出报告，确保没有泄露敏感信息

## 测试覆盖

项目包含完整的单元测试:
- `test_cli.py` - CLI 接口测试
- `test_log_parser.py` - 日志解析测试
- `test_chunker.py` - 分块逻辑测试
- `test_masker.py` - 数据脱敏测试
- `test_bailian_client.py` - API 客户端测试
- `test_analyzer.py` - 分析器测试

运行测试:
```bash
pytest tests/
```

## 总结

MTK Log LLM Inspector 是一个设计良好、模块化的日志分析工具。它充分利用了大语言模型的理解能力，将复杂的日志分析任务自动化。通过滑动窗口、状态合并等技术，系统能够处理任意长度的日志文件，生成结构化的分析结果。

### 核心优势
1. **自动化**: 无需手动检查海量日志
2. **智能**: 利用 LLM 理解复杂的日志模式
3. **灵活**: 可配置的参数和模块化设计
4. **安全**: 内置数据脱敏和密钥保护
5. **完整**: 从输入到输出的完整工作流

### 适用场景
- Android 音频系统调试
- 自动化测试中的状态验证
- 长时间运行的日志分析
- 音频问题的根因分析
- 批量日志处理和报告生成
