# MTK Log LLM Inspector

使用文本大模型分析安卓系统音频问题 / Analyze Android audio issues using Alibaba Cloud Bailian LLM.

A CLI tool that analyzes Android logcat files and uses Alibaba Cloud Bailian (Qwen) LLM to infer audio playback states.

## Features

- 🔍 **Automatic Audio Log Filtering**: Pre-filters logcat for audio-related lines
- 🪟 **Sliding Window Analysis**: Processes logs in configurable chunks with overlap
- 🤖 **LLM-Powered State Detection**: Uses Qwen to identify PLAYING/MUTED/UNKNOWN states
- 📊 **Segment Merging**: Combines consecutive windows with the same state
- 📝 **Dual Output**: Generates both JSON and Markdown reports
- 🔒 **Data Masking**: Optional masking of sensitive information (emails, IPs, serials)
- 🐛 **Debug Mode**: Saves API request/response for troubleshooting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Yang-QZ/mtk-log-llm-inspector.git
cd mtk-log-llm-inspector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Alibaba Cloud Bailian API key:
```bash
export BAILIAN_API_KEY="your-api-key-here"
```

Optional environment variables:
```bash
export BAILIAN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"  # Default
export BAILIAN_MODEL="qwen-plus"  # Default
```

## Usage

### Basic Command

```bash
python -m src.cli analyze --log <path-to-log> --out <output-directory>
```

### Full Options

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

### Options

- `--log PATH`: Path to input log file (required)
- `--out PATH`: Path to output directory (required)
- `--chunk-size N`: Number of lines per analysis window (default: 200)
- `--overlap M`: Number of overlapping lines between windows (default: 50)
- `--model MODEL`: LLM model name (default: qwen-plus)
- `--debug`: Enable debug mode (saves request/response JSON files)
- `--mask`: Enable data masking for sensitive information

## Example

```bash
# Analyze the demo log
python -m src.cli analyze --log samples/demo.log --out output/

# With debug and masking enabled
python -m src.cli analyze --log samples/demo.log --out output/ --debug --mask
```

## Output

The tool generates two reports in the output directory:

### 1. `report.json` - Complete Analysis Data

```json
{
  "metadata": {
    "log_file": "/path/to/log.txt",
    "timestamp": "2024-01-06T10:00:00",
    "chunk_size": 200,
    "overlap": 50,
    "model": "qwen-plus",
    "total_windows": 5,
    "total_lines": 847
  },
  "summary": {
    "total_windows": 5,
    "total_segments": 3,
    "states_distribution": {
      "PLAYING": 2,
      "MUTED": 1,
      "UNKNOWN": 0
    }
  },
  "window_results": [...],
  "merged_segments": [...]
}
```

### 2. `report.md` - Human-Readable Summary

```markdown
# Audio State Analysis Report

**Analysis Time:** 2024-01-06T10:00:00
**Log File:** samples/demo.log
**Total Windows:** 5
**Total Segments:** 3

## Segments Summary

### Segment 1: PLAYING
- **Windows:** 0 to 2 (3 windows)
- **Average Confidence:** 0.88

**Key Evidence (up to 5 lines):**
...
```

### Debug Output (with `--debug`)

When debug mode is enabled, additional files are saved to `out/debug/`:
- `window_0_request.json` - API request for window 0 (auth redacted)
- `window_0_response.json` - API response for window 0
- ... (one pair per window)

## Project Structure

```
mtk-log-llm-inspector/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── bailian_client.py   # Alibaba Cloud Bailian API client
│   ├── log_parser.py       # Log file parsing and filtering
│   ├── chunker.py          # Window chunking with overlap
│   ├── masker.py           # Sensitive data masking
│   └── analyzer.py         # Analysis and segment merging
├── tests/
│   ├── test_bailian_client.py
│   ├── test_log_parser.py
│   ├── test_chunker.py
│   ├── test_masker.py
│   └── test_analyzer.py
├── docs/
│   └── prompt.md           # LLM system prompt
├── samples/
│   └── demo.log            # Sample logcat file
├── requirements.txt
└── README.md
```

## How It Works

1. **Parse & Filter**: Reads the log file and filters for audio-related lines using configurable tag matching
2. **Chunk**: Splits filtered lines into overlapping windows (default: 200 lines with 50-line overlap)
3. **Analyze**: For each window, sends to Bailian LLM with system prompt to get structured JSON response
4. **Merge**: Combines consecutive windows with the same state into segments
5. **Report**: Generates JSON and Markdown reports with analysis results

## Audio State Detection

The LLM classifies each window into one of three states:

- **PLAYING**: Audio is actively playing (streams active, unmuted, routing established)
- **MUTED**: Audio is muted or streams are inactive/stopped
- **UNKNOWN**: Insufficient information or conflicting signals

Each analysis includes:
- State classification
- Confidence score (0.0-1.0)
- Reasoning
- Supporting evidence (up to 5 key log lines)
- Suggested next actions

## Running Tests

```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Input Format

The tool works with standard Android logcat output (threadtime format):
```
01-06 10:15:23.456  1234  1235 I AudioFlinger: Track started
```

But it also works with any generic text file. The audio tag filtering is optional and configurable.

## Data Masking

When `--mask` is enabled, the following patterns are masked:
- Email addresses → `[EMAIL]`
- IPv4 addresses → `[IPv4]`
- IPv6 addresses → `[IPv6]`
- MAC addresses → `[MAC]`
- Serial numbers (with keyword) → `[SERIAL]`

## Security

- **Never commit API keys**: Use environment variables only
- **Auth headers redacted**: Debug mode automatically redacts authorization headers
- **Optional masking**: Enable `--mask` to remove sensitive data before sending to LLM

## Limitations

- Offline file analysis only (no real-time streaming)
- No direct adb integration (export logs first)
- Depends on Alibaba Cloud Bailian API availability
- Analysis quality depends on LLM model capabilities

## License

See repository license.

## Contributing

Contributions welcome! Please ensure tests pass before submitting PRs:
```bash
pytest tests/
```
